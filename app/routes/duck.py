from flask import Blueprint, render_template, redirect, url_for, jsonify, request, send_file
from datetime import datetime
from pathlib import Path
from ..config import DUCK_TYPES, TRAINED_MODELS_DIR
from ..services.open_duck_mini_playground import OpenDuckPlaygroundService
from ..services.awd import AWDService
from ..services.deployment import DeploymentService
from ..services.reference_motion_generation import ReferenceMotionGenerationService
import logging

class DuckBlueprint(Blueprint):
    """Blueprint for handling duck-related routes and views."""
    
    def __init__(self, name, import_name, **kwargs):
        super().__init__(name, import_name, **kwargs)
        self.workspace_root = Path(__file__).parent.parent.parent
        
        # Initialize logger
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Initialize services
        self.playground_service = OpenDuckPlaygroundService(self.workspace_root)
        self.awd_service = AWDService(self.workspace_root)
        self.deployment_service = DeploymentService(self.workspace_root)
        self.motion_service = ReferenceMotionGenerationService(self.workspace_root)
        
        # Register routes
        self.register_routes()
        
    def get_trained_models(self, duck_type, variant):
        """Get list of trained models for a specific duck type and variant."""
        models_dir = TRAINED_MODELS_DIR / duck_type / variant
        if not models_dir.exists():
            return []
        
        models = []
        for model_file in models_dir.glob('*.onnx'):
            models.append({
                'name': model_file.name,
                'path': str(model_file),
                'date': datetime.fromtimestamp(model_file.stat().st_mtime)
            })
        return sorted(models, key=lambda x: x['date'], reverse=True)
        
    def register_routes(self):
        """Register all routes for this blueprint."""
        
        @self.route('/')
        def duck_page():
            """Render the page for a specific duck type."""
            duck_type = self.name
            if duck_type not in DUCK_TYPES:
                return redirect(url_for('main.index'))
            
            # Get the variant from query parameters, default to first variant
            variant_id = request.args.get('variant', list(DUCK_TYPES[duck_type]['variants'].keys())[0])
            variant = DUCK_TYPES[duck_type]['variants'].get(variant_id)
            
            if not variant:
                return redirect(url_for('main.index'))
            
            # Create a duck object with all necessary information
            duck_data = {
                'name': DUCK_TYPES[duck_type]['name'],
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant['name'],
                    'model_path': variant['model_path'],
                    'description': variant['description']
                },
                'features': [
                    'Advanced walking dynamics',
                    'Real-time motion planning',
                    'Terrain adaptation',
                    'Energy optimization'
                ],
                'specifications': [
                    {'title': 'Height', 'value': '1.2m'},
                    {'title': 'Weight', 'value': '5kg'},
                    {'title': 'Battery Life', 'value': '4 hours'}
                ],
            }
            
            trained_models = self.get_trained_models(duck_type, variant_id)
            return render_template('duck_page.html', 
                                duck=duck_data,
                                trained_models=trained_models,
                                variants=DUCK_TYPES[duck_type]['variants'])
                                
        @self.route('/train', methods=['POST'])
        def train_duck():
            """Start training for a specific duck type."""
            try:
                data = request.get_json()
                variant = data.get('variant')
                num_envs = data.get('num_envs', 1)
                motion_file = data.get('motion_file')
                framework = data.get('framework', 'playground')
                
                if framework == 'playground':
                    success, message, output = self.playground_service.train_model(
                        duck_type=self.name,
                        variant=variant,
                        num_envs=num_envs,
                        motion_file=motion_file
                    )
                else:
                    success, message, output = self.awd_service.train_model(
                        duck_type=self.name,
                        variant=variant,
                        num_envs=num_envs,
                        motion_file=motion_file
                    )
                    
                return jsonify({
                    'success': success,
                    'message': message,
                    'output': output
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error starting training: {str(e)}'
                })
                
        @self.route('/generate_motion', methods=['POST'])
        def generate_motion():
            """Generate motion for a specific duck type."""
            try:
                # Debug incoming request
                self.logger.debug(f"Incoming motion generation request for duck type: {self.name}")
                self.logger.debug(f"Request form data: {request.form}")
                self.logger.debug(f"Request args: {request.args}")
                
                # Handle form data instead of JSON
                data = request.form.to_dict()
                variant = request.args.get('variant')
                mode = data.get('mode', 'auto')
                
                self.logger.info(f"Processing motion generation request - Duck: {self.name}, Variant: {variant}, Mode: {mode}")
                self.logger.debug(f"Form parameters: {data}")
                
                # Remove mode from data since we're passing it separately
                if 'mode' in data:
                    del data['mode']
                    
                # Call the service with all the parameters
                self.logger.debug(f"Calling motion service with params: duck_type={self.name}, variant={variant}, mode={mode}, and {len(data)} additional parameters")
                success, message, output = self.motion_service.generate_motion(
                    duck_type=self.name,
                    variant=variant,
                    mode=mode,
                    **data  # Pass remaining form data as params
                )
                
                self.logger.debug(f"Service returned: success={success}, message={message}")
                
                if not success:
                    self.logger.error(f"Motion generation failed: {message}")
                    if output and isinstance(output, dict):
                        self.logger.error(f"Error details: {output}")
                    return jsonify({
                        'success': False,
                        'error': message,  # Using 'error' instead of 'message' to match frontend expectations
                        'details': output
                    })
                
                self.logger.info(f"Motion generation completed successfully")
                return jsonify({
                    'success': success,
                    'message': message,
                    'motion_data': output  # Change 'output' to 'motion_data' to match frontend expectation
                })
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.logger.error(f"Unexpected error in motion generation: {str(e)}")
                self.logger.error(f"Traceback: {error_details}")
                return jsonify({
                    'success': False,
                    'error': f"Error generating motion: {str(e)}",  # Using 'error' instead of 'message'
                    'details': {
                        'traceback': error_details,
                        'error': str(e)
                    }
                })
                
        @self.route('/deploy', methods=['POST'])
        def deploy_duck():
            """Deploy a model to a duck device."""
            try:
                data = request.get_json()
                variant = data.get('variant')
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
                
        @self.route('/connect', methods=['POST'])
        def connect_duck():
            """Connect to a duck device."""
            try:
                data = request.get_json()
                variant = data.get('variant')
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
                
        @self.route('/status', methods=['GET'])
        def get_duck_status():
            """Get status of a duck device."""
            try:
                variant = request.args.get('variant')
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

        @self.route('/check_motion_files', methods=['GET'])
        def check_motion_files():
            """Check if motion files are available for the current duck type."""
            try:
                variant = request.args.get('variant', None)
                duck_type = request.path.split('/')[1]
                self.logger.debug(f"check_motion_files called for {duck_type} (variant: {variant})")
                
                # Get internal name based on duck_type and variant
                internal_name = self.get_internal_duck_name(duck_type, variant)
                self.logger.debug(f"Mapped to internal duck name: {internal_name}")
                
                # Log request details for debugging
                debug_info = {
                    "url_path": request.path,
                    "duck_type": duck_type,
                    "variant": variant,
                    "internal_name": internal_name,
                    "request_args": dict(request.args),
                    "request_headers": dict(request.headers)
                }
                self.logger.debug(f"Request details: {debug_info}")
                
                # Check for motion files
                files = self.motion_service.list_motion_files(internal_name)
                self.logger.debug(f"Found motion files: {files}")
                
                return jsonify({
                    "success": True,
                    "files": files,
                    "debug_info": debug_info
                })
            except Exception as e:
                self.logger.error(f"Error checking motion files: {str(e)}", exc_info=True)
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "debug_info": {
                        "exception": str(e),
                        "traceback": traceback.format_exc()
                    }
                })
        
        @self.route('/check_training_files', methods=['GET'])
        def check_training_files():
            """Check if training files are available for the current duck type."""
            try:
                variant = request.args.get('variant', None)
                duck_type = request.path.split('/')[1]
                self.logger.debug(f"check_training_files called for {duck_type} (variant: {variant})")
                
                # Get internal name based on duck_type and variant
                internal_name = self.get_internal_duck_name(duck_type, variant)
                self.logger.debug(f"Mapped to internal duck name: {internal_name}")
                
                # Debug info
                debug_info = {
                    "url_path": request.path,
                    "duck_type": duck_type,
                    "variant": variant,
                    "internal_name": internal_name
                }
                
                # Check for training files
                # You would implement this method in your service
                files = self.motion_service.list_training_files(internal_name)
                
                return jsonify({
                    "success": True,
                    "files": files,
                    "debug_info": debug_info
                })
            except Exception as e:
                self.logger.error(f"Error checking training files: {str(e)}", exc_info=True)
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "debug_info": {
                        "exception": str(e),
                        "traceback": traceback.format_exc()
                    }
                })
        
        @self.route('/check_testing_files', methods=['GET'])
        def check_testing_files():
            """Check if testing files are available for the current duck type."""
            try:
                variant = request.args.get('variant', None)
                duck_type = request.path.split('/')[1]
                self.logger.debug(f"check_testing_files called for {duck_type} (variant: {variant})")
                
                # Get internal name based on duck_type and variant
                internal_name = self.get_internal_duck_name(duck_type, variant)
                self.logger.debug(f"Mapped to internal duck name: {internal_name}")
                
                # Debug info
                debug_info = {
                    "url_path": request.path,
                    "duck_type": duck_type,
                    "variant": variant,
                    "internal_name": internal_name
                }
                
                # Check for testing files
                # You would implement this method in your service
                files = self.motion_service.list_testing_files(internal_name)
                
                return jsonify({
                    "success": True,
                    "files": files,
                    "debug_info": debug_info
                })
            except Exception as e:
                self.logger.error(f"Error checking testing files: {str(e)}", exc_info=True)
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "debug_info": {
                        "exception": str(e),
                        "traceback": traceback.format_exc()
                    }
                })

        @self.route('/download_motion', methods=['POST'])
        def download_motion():
            """Download the latest generated motion file."""
            try:
                variant = request.args.get('variant')
                
                # Find the latest motion file
                motion_files = self.motion_service.list_motion_files(
                    duck_type=self.name,
                    variant=variant
                )
                
                if not motion_files:
                    return jsonify({
                        'success': False,
                        'error': 'No motion files available'
                    }), 404
                
                # Get the most recent file
                latest_file = motion_files[0]
                file_path = self.workspace_root / latest_file['path']
                
                if not file_path.exists():
                    self.logger.error(f"Motion file does not exist: {file_path}")
                    return jsonify({
                        'success': False,
                        'error': 'Motion file not found'
                    }), 404
                
                self.logger.info(f"Downloading motion file: {file_path}")
                
                # Return the file as an attachment
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=latest_file['name'],
                    mimetype='application/json'
                )
                
            except Exception as e:
                self.logger.error(f"Error downloading motion file: {str(e)}")
                self.logger.error(traceback.format_exc())
                return jsonify({
                    'success': False,
                    'error': f'Error downloading motion file: {str(e)}'
                }), 500

    def get_internal_duck_name(self, duck_type, variant):
        """
        Maps URL path duck type and variant to internal duck name used in the system.
        """
        if duck_type == 'bdx':
            if variant == 'go2':
                return 'go2_bdx'
            elif variant == 'cybergear':
                return 'cybergear_bdx'
            elif variant == 'servo':
                return 'servo_bdx'
            else:  # Default is go1 or any unknown variant
                return 'go_bdx'
        elif duck_type == 'open_duck_mini':
            if variant == 'v1':
                return 'open_duck_mini_v1'
            elif variant == 'v3':
                return 'open_duck_mini_v3'
            else:  # Default is v2 or any unknown variant
                return 'open_duck_mini_v2'
        
        # If no mapping exists, return the duck_type as is
        self.logger.warning(f"No internal name mapping for duck_type: {duck_type}, variant: {variant}")
        return duck_type

# Create blueprint instance
duck = DuckBlueprint('duck', __name__) 
