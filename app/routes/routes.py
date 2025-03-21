from flask import Blueprint, request, jsonify, current_app, url_for
from pathlib import Path
from ..services.open_duck_mini_playground import OpenDuckPlaygroundService
from ..services.awd import AWDService
from ..services.deployment import DeploymentService
from ..services.reference_motion_generation import ReferenceMotionGenerationService
from ..config import duck_config

class DuckRoutes:
    """Class to handle all duck-related routes."""
    
    def __init__(self, app):
        self.app = app
        self.workspace_root = Path(app.root_path).parent
        
        # Initialize services
        self.playground_service = OpenDuckPlaygroundService(self.workspace_root)
        self.awd_service = AWDService(self.workspace_root)
        self.deployment_service = DeploymentService(self.workspace_root)
        self.motion_service = ReferenceMotionGenerationService(self.workspace_root)
        
        # Register routes
        self.register_routes()
        
    def get_internal_duck_type(self, duck_type, variant=None):
        """Get the internal duck type name based on the URL path and variant."""
        if variant:
            return duck_config.get_internal_name(duck_type, variant)
        
        # If no variant specified, use the first variant's internal name as default
        duck_type_config = duck_config.get_duck_type(duck_type)
        if duck_type_config and 'variants' in duck_type_config:
            first_variant_id = next(iter(duck_type_config['variants'].keys()))
            return duck_config.get_internal_name(duck_type, first_variant_id)
            
        return None
        
    def register_routes(self):
        """Register all routes for the application."""
        
        # Duck type listing route
        @self.app.route('/api/duck_types', methods=['GET'])
        def list_duck_types():
            duck_types = duck_config.list_duck_types()
            return jsonify({
                'success': True,
                'duck_types': duck_types
            })
            
        # Duck variant listing route
        @self.app.route('/api/duck_types/<duck_type>/variants', methods=['GET'])
        def list_variants(duck_type):
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                return jsonify({
                    'success': False,
                    'error': f'Duck type {duck_type} not found'
                }), 404
                
            variants = []
            for variant_id, variant in duck_type_config.get('variants', {}).items():
                variants.append({
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'description': variant.get('description', ''),
                    'internal_name': variant.get('internal_name', ''),
                    'model_path': variant.get('model_path', '')
                })
                
            return jsonify({
                'success': True,
                'variants': variants
            })
        
        # Training routes
        @self.app.route('/api/train', methods=['POST'])
        def start_training():
            try:
                data = request.get_json()
                duck_type = data.get('duck_type')
                variant = data.get('variant')
                num_envs = data.get('num_envs', 1)
                motion_file = data.get('motion_file')
                framework = data.get('framework', 'playground')  # or 'awd'
                
                internal_duck_type = self.get_internal_duck_type(duck_type, variant)
                if not internal_duck_type:
                    return jsonify({'success': False, 'error': 'Invalid duck type or variant'}), 400
                
                if framework == 'playground':
                    success, message, output = self.playground_service.train_model(
                        duck_type=internal_duck_type,
                        num_envs=num_envs,
                        motion_file=motion_file
                    )
                else:
                    success, message, output = self.awd_service.train_model(
                        duck_type=internal_duck_type,
                        num_envs=num_envs,
                        motion_file=motion_file
                    )
                    
                return jsonify({
                    'success': success,
                    'message': message,
                    'output': output
                })
                
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
                
        # Motion generation routes
        @self.app.route('/<duck_type>/generate_motion', methods=['POST'])
        def generate_motion(duck_type):
            try:
                data = request.form.to_dict()
                variant = request.args.get('variant')
                mode = data.get('mode', 'auto')
                
                # Enhanced logging
                current_app.logger.info(f"Motion generation request received - Duck type: {duck_type}, Variant: {variant}, Mode: {mode}")
                current_app.logger.debug(f"Request form data: {data}")
                current_app.logger.debug(f"Request args: {request.args}")
                current_app.logger.debug(f"Request headers: {dict(request.headers)}")
                
                # Get internal name from config
                if not duck_config.get_duck_type(duck_type):
                    error_msg = f"Invalid duck type ({duck_type})"
                    current_app.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg,
                        'details': {
                            'duck_type': duck_type,
                            'available_types': [dt['id'] for dt in duck_config.list_duck_types()]
                        }
                    }), 400
                
                if variant and not duck_config.get_variant(duck_type, variant):
                    error_msg = f"Invalid variant ({variant}) for duck type ({duck_type})"
                    current_app.logger.error(error_msg)
                    duck_type_config = duck_config.get_duck_type(duck_type)
                    return jsonify({
                        'success': False,
                        'error': error_msg,
                        'details': {
                            'duck_type': duck_type,
                            'variant': variant,
                            'available_variants': list(duck_type_config.get('variants', {}).keys())
                        }
                    }), 400

                internal_name = self.get_internal_duck_type(duck_type, variant)
                current_app.logger.info(f"Using internal duck name: {internal_name} (from {duck_type}:{variant})")
                
                # Log parameters being passed to the service
                service_params = data.copy()
                current_app.logger.debug(f"Calling motion_service.generate_motion with params: duck_type={internal_name}, mode={mode}, **{service_params}")
                
                success, message, motion_data = self.motion_service.generate_motion(
                    duck_type=internal_name,
                    variant=variant,
                    mode=mode,
                    **data
                )
                
                if not success:
                    current_app.logger.error(f"Motion generation failed: {message}")
                    if motion_data and isinstance(motion_data, dict):
                        current_app.logger.error(f"Detailed output: {motion_data}")
                        return jsonify({
                            'success': False,
                            'error': message,
                            'details': motion_data
                        }), 500
                    else:
                        return jsonify({
                            'success': False,
                            'error': message,
                            'details': {
                                'error': str(motion_data) if motion_data else 'No additional details available'
                            }
                        }), 500
                
                current_app.logger.info(f"Motion generation successful: {message}")
                return jsonify({
                    'success': True,
                    'message': message,
                    'motion_data': motion_data
                })
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                current_app.logger.error(f"Unexpected error in motion generation: {str(e)}")
                current_app.logger.error(f"Traceback: {error_details}")
                return jsonify({
                    'success': False, 
                    'error': str(e),
                    'details': {
                        'traceback': error_details,
                        'error': str(e)
                    }
                }), 500
                
        # Deployment routes
        @self.app.route('/api/deploy', methods=['POST'])
        def deploy_model():
            try:
                data = request.get_json()
                model_path = data.get('model_path')
                remote_path = data.get('remote_path')
                device_type = data.get('device_type', 'serial')
                
                success, message = self.deployment_service.deploy_model(
                    model_path=model_path,
                    remote_path=remote_path,
                    device_type=device_type
                )
                
                return jsonify({
                    'success': success,
                    'message': message
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error deploying model: {str(e)}'
                })
                
        # Device connection routes
        @self.app.route('/api/connect', methods=['POST'])
        def connect_device():
            try:
                data = request.get_json()
                device_type = data.get('device_type', 'serial')
                
                if device_type == 'serial':
                    port = data.get('port')
                    baudrate = data.get('baudrate', 115200)
                    success, message = self.deployment_service.connect_serial(
                        port=port,
                        baudrate=baudrate
                    )
                else:
                    hostname = data.get('hostname')
                    username = data.get('username')
                    password = data.get('password')
                    key_filename = data.get('key_filename')
                    success, message = self.deployment_service.connect_ssh(
                        hostname=hostname,
                        username=username,
                        password=password,
                        key_filename=key_filename
                    )
                    
                return jsonify({
                    'success': success,
                    'message': message
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error connecting to device: {str(e)}'
                })
                
        # Device status route
        @self.app.route('/api/device_status', methods=['GET'])
        def get_device_status():
            try:
                device_type = request.args.get('device_type', 'serial')
                success, message, status = self.deployment_service.get_device_status(device_type)
                
                return jsonify({
                    'success': success,
                    'message': message,
                    'status': status
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error getting device status: {str(e)}'
                }) 