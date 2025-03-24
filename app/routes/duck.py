from flask import Blueprint, render_template, redirect, url_for, jsonify, request, send_file
from datetime import datetime
from pathlib import Path
from ..config import TRAINED_MODELS_DIR, duck_config
from ..services.open_duck_mini_playground import OpenDuckPlaygroundService
from ..services.awd import AWDService
from ..services.deployment import DeploymentService
from ..services.reference_motion_generation import ReferenceMotionGenerationService
import logging
import os

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
            
            # Check if duck type exists in config
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                self.logger.warning(f"Invalid duck type requested: {duck_type}")
                return redirect(url_for('main.index'))
            
            # Get the variant from query parameters, default to first variant
            variants = duck_type_config.get('variants', {})
            if not variants:
                self.logger.warning(f"No variants found for duck type: {duck_type}")
                return redirect(url_for('main.index'))
                
            variant_id = request.args.get('variant', list(variants.keys())[0])
            variant = variants.get(variant_id)
            
            if not variant:
                self.logger.warning(f"Invalid variant requested: {variant_id} for duck type: {duck_type}")
                return redirect(url_for('main.index'))
            
            # Create a duck object with all necessary information
            duck_data = {
                'name': duck_type_config.get('name', duck_type),
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'model_path': variant.get('model_path', ''),
                    'description': variant.get('description', '')
                },
                'features': duck_type_config.get('features', [
                    'Advanced walking dynamics',
                    'Real-time motion planning',
                    'Terrain adaptation',
                    'Energy optimization'
                ]),
                'specifications': duck_type_config.get('specifications', [
                    {'title': 'Height', 'value': '1.2m'},
                    {'title': 'Weight', 'value': '5kg'},
                    {'title': 'Battery Life', 'value': '4 hours'}
                ]),
            }
            
            # Get internal name for this duck type and variant
            duck_data['internal_name'] = self.get_internal_duck_name(duck_type, variant_id)
            
            trained_models = self.get_trained_models(duck_type, variant_id)
            return render_template('duck_page.html', 
                                duck=duck_data,
                                trained_models=trained_models,
                                variants=variants)

        @self.route('/stl_models')
        def stl_models():
            """Render the STL models page for a specific duck type."""
            duck_type = self.name
            variant_id = request.args.get('variant')
            
            # Get duck type config and validate
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                return redirect(url_for('main.index'))
            
            # Get variant info
            variants = duck_type_config.get('variants', {})
            if not variants:
                return redirect(url_for('main.index'))
            
            if not variant_id:
                variant_id = list(variants.keys())[0]
            
            variant = variants.get(variant_id)
            if not variant:
                return redirect(url_for('main.index'))
            
            # Create duck data object
            duck_data = {
                'name': duck_type_config.get('name', duck_type),
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'model_path': variant.get('model_path', ''),
                    'description': variant.get('description', '')
                }
            }
            
            # Get STL parts data from config
            stl_parts = duck_type_config.get('stl_parts', [])
            
            return render_template('duck_droids/stl_models.html',
                                duck=duck_data,
                                stl_parts=stl_parts,
                                variants=variants)

        @self.route('/bom')
        def bom():
            """Render the Bill of Materials page for a specific duck type."""
            duck_type = self.name
            variant_id = request.args.get('variant')
            
            # Get duck type config and validate
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                return redirect(url_for('main.index'))
            
            # Get variant info
            variants = duck_type_config.get('variants', {})
            if not variants:
                return redirect(url_for('main.index'))
            
            if not variant_id:
                variant_id = list(variants.keys())[0]
            
            variant = variants.get(variant_id)
            if not variant:
                return redirect(url_for('main.index'))
            
            # Create duck data object
            duck_data = {
                'name': duck_type_config.get('name', duck_type),
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'model_path': variant.get('model_path', ''),
                    'description': variant.get('description', '')
                }
            }
            
            # Get BOM data from config
            required_components = duck_type_config.get('required_components', [])
            optional_components = duck_type_config.get('optional_components', [])
            
            return render_template('duck_droids/bom.html',
                                duck=duck_data,
                                required_components=required_components,
                                optional_components=optional_components,
                                variants=variants)

        @self.route('/playground')
        def playground():
            """Render the playground page for testing the droid."""
            duck_type = self.name
            variant_id = request.args.get('variant')
            
            # Get duck type config and validate
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                return redirect(url_for('main.index'))
            
            # Get variant info
            variants = duck_type_config.get('variants', {})
            if not variants:
                return redirect(url_for('main.index'))
            
            if not variant_id:
                variant_id = list(variants.keys())[0]
            
            variant = variants.get(variant_id)
            if not variant:
                return redirect(url_for('main.index'))
            
            # Create duck data object
            duck_data = {
                'name': duck_type_config.get('name', duck_type),
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'model_path': variant.get('model_path', ''),
                    'description': variant.get('description', '')
                }
            }
            
            # Get trained models for this variant
            trained_models = self.get_trained_models(duck_type, variant_id)
            
            return render_template('duck_droids/playground.html',
                                duck=duck_data,
                                trained_models=trained_models,
                                variants=variants)

        @self.route('/training')
        def training():
            """Render the training page for a specific duck type."""
            duck_type = self.name
            variant_id = request.args.get('variant')
            
            # Get duck type config and validate
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                return redirect(url_for('main.index'))
            
            # Get variant info
            variants = duck_type_config.get('variants', {})
            if not variants:
                return redirect(url_for('main.index'))
            
            if not variant_id:
                variant_id = list(variants.keys())[0]
            
            variant = variants.get(variant_id)
            if not variant:
                return redirect(url_for('main.index'))
            
            # Create duck data object
            duck_data = {
                'name': duck_type_config.get('name', duck_type),
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'model_path': variant.get('model_path', ''),
                    'description': variant.get('description', '')
                }
            }
            
            # Get motion files for this variant
            internal_name = self.get_internal_duck_name(duck_type, variant_id)
            motion_files = self.motion_service.list_motion_files(internal_name)
            
            return render_template('duck_droids/training.html',
                                duck=duck_data,
                                motion_files=motion_files,
                                variants=variants)

        @self.route('/updates')
        def updates():
            """Render the updates page for a specific duck type."""
            duck_type = self.name
            variant_id = request.args.get('variant')
            
            # Get duck type config and validate
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                return redirect(url_for('main.index'))
            
            # Get variant info
            variants = duck_type_config.get('variants', {})
            if not variants:
                return redirect(url_for('main.index'))
            
            if not variant_id:
                variant_id = list(variants.keys())[0]
            
            variant = variants.get(variant_id)
            if not variant:
                return redirect(url_for('main.index'))
            
            # Create duck data object
            duck_data = {
                'name': duck_type_config.get('name', duck_type),
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'model_path': variant.get('model_path', ''),
                    'description': variant.get('description', '')
                }
            }
            
            # Get trained models for this variant
            trained_models = self.get_trained_models(duck_type, variant_id)
            
            return render_template('duck_droids/updates.html',
                                duck=duck_data,
                                trained_models=trained_models,
                                variants=variants)

        @self.route('/troubleshooting')
        def troubleshooting():
            """Render the troubleshooting page for a specific duck type."""
            duck_type = self.name
            variant_id = request.args.get('variant')
            
            # Get duck type config and validate
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                return redirect(url_for('main.index'))
            
            # Get variant info
            variants = duck_type_config.get('variants', {})
            if not variants:
                return redirect(url_for('main.index'))
            
            if not variant_id:
                variant_id = list(variants.keys())[0]
            
            variant = variants.get(variant_id)
            if not variant:
                return redirect(url_for('main.index'))
            
            # Create duck data object
            duck_data = {
                'name': duck_type_config.get('name', duck_type),
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'model_path': variant.get('model_path', ''),
                    'description': variant.get('description', '')
                }
            }
            
            # Get troubleshooting data from config
            common_issues = duck_type_config.get('common_issues', [])
            
            return render_template('duck_droids/troubleshooting.html',
                                duck=duck_data,
                                common_issues=common_issues,
                                variants=variants)

        @self.route('/assembly')
        def assembly():
            """Render the assembly guide page for a specific duck type."""
            duck_type = self.name
            variant_id = request.args.get('variant')
            
            # Get duck type config and validate
            duck_type_config = duck_config.get_duck_type(duck_type)
            if not duck_type_config:
                return redirect(url_for('main.index'))
            
            # Get variant info
            variants = duck_type_config.get('variants', {})
            if not variants:
                return redirect(url_for('main.index'))
            
            if not variant_id:
                variant_id = list(variants.keys())[0]
            
            variant = variants.get(variant_id)
            if not variant:
                return redirect(url_for('main.index'))
            
            # Create duck data object
            duck_data = {
                'name': duck_type_config.get('name', duck_type),
                'type': duck_type,
                'variant': {
                    'id': variant_id,
                    'name': variant.get('name', variant_id),
                    'model_path': variant.get('model_path', ''),
                    'description': variant.get('description', '')
                }
            }
            
            # Get assembly steps from config
            assembly_steps = duck_type_config.get('assembly_steps', [])
            
            return render_template('duck_droids/assembly.html',
                                duck=duck_data,
                                assembly_steps=assembly_steps,
                                variants=variants)

        @self.route('/train', methods=['POST'])
        def train_duck():
            """Start training for a specific duck type."""
            try:
                data = request.get_json()
                variant = data.get('variant')
                num_envs = data.get('num_envs', 1)
                motion_file = data.get('motion_file')
                framework = data.get('framework', 'playground')
                
                # Get the internal duck name using duck_config
                internal_name = self.get_internal_duck_name(self.name, variant)
                if not internal_name:
                    self.logger.error(f"Invalid duck type or variant: {self.name}/{variant}")
                    return jsonify({
                        'success': False,
                        'message': f'Invalid duck type or variant: {self.name}/{variant}'
                    }), 400
                
                self.logger.info(f"Starting training for {self.name} (variant: {variant}, internal: {internal_name}) with {framework}")
                
                if framework == 'playground':
                    success, message, output = self.playground_service.train_model(
                        duck_type=internal_name,
                        num_envs=num_envs,
                        motion_file=motion_file
                    )
                else:
                    success, message, output = self.awd_service.train_model(
                        duck_type=internal_name,
                        num_envs=num_envs,
                        motion_file=motion_file
                    )
                    
                return jsonify({
                    'success': success,
                    'message': message,
                    'output': output
                })
                
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.logger.error(f"Unexpected error in training: {str(e)}")
                self.logger.error(f"Traceback: {error_details}")
                return jsonify({
                    'success': False,
                    'message': f'Error starting training: {str(e)}',
                    'details': {
                        'traceback': error_details,
                        'error': str(e)
                    }
                }), 500
                
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
                
                # Validate duck type and variant
                if not duck_config.get_duck_type(self.name):
                    error_msg = f"Invalid duck type ({self.name})"
                    self.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg,
                        'details': {
                            'duck_type': self.name,
                            'available_types': [dt['id'] for dt in duck_config.list_duck_types()]
                        }
                    }), 400
                
                if variant and not duck_config.get_variant(self.name, variant):
                    error_msg = f"Invalid variant ({variant}) for duck type ({self.name})"
                    self.logger.error(error_msg)
                    duck_type_config = duck_config.get_duck_type(self.name)
                    return jsonify({
                        'success': False,
                        'error': error_msg,
                        'details': {
                            'duck_type': self.name,
                            'variant': variant,
                            'available_variants': list(duck_type_config.get('variants', {}).keys())
                        }
                    }), 400
                
                # Get internal duck name
                internal_name = self.get_internal_duck_name(self.name, variant)
                if not internal_name:
                    error_msg = f"Could not determine internal name for {self.name}/{variant}"
                    self.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                
                self.logger.info(f"Using internal duck name: {internal_name}")
                
                # Remove mode from data since we're passing it separately
                if 'mode' in data:
                    del data['mode']
                    
                # Call the service with all the parameters
                self.logger.debug(f"Calling motion service with params: duck_type={internal_name}, mode={mode}, and {len(data)} additional parameters")
                success, message, output = self.motion_service.generate_motion(
                    duck_type=internal_name,
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
                
                # Validate duck type and variant
                if not duck_config.get_duck_type(duck_type):
                    error_msg = f"Invalid duck type ({duck_type})"
                    self.logger.error(error_msg)
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
                    self.logger.error(error_msg)
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
                
                # Get internal name based on duck_type and variant
                internal_name = self.get_internal_duck_name(duck_type, variant)
                if not internal_name:
                    error_msg = f"Could not determine internal name for {duck_type}/{variant}"
                    self.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                    
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
                import traceback
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
                
                # Validate duck type and variant
                if not duck_config.get_duck_type(duck_type):
                    error_msg = f"Invalid duck type ({duck_type})"
                    self.logger.error(error_msg)
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
                    self.logger.error(error_msg)
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
                
                # Get internal name based on duck_type and variant
                internal_name = self.get_internal_duck_name(duck_type, variant)
                if not internal_name:
                    error_msg = f"Could not determine internal name for {duck_type}/{variant}"
                    self.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                    
                self.logger.debug(f"Mapped to internal duck name: {internal_name}")
                
                # Debug info
                debug_info = {
                    "url_path": request.path,
                    "duck_type": duck_type,
                    "variant": variant,
                    "internal_name": internal_name,
                    "request_args": dict(request.args)
                }
                
                # Check for training files
                files = self.motion_service.list_training_files(internal_name)
                self.logger.debug(f"Found training files: {files}")
                
                return jsonify({
                    "success": True,
                    "files": files,
                    "debug_info": debug_info
                })
            except Exception as e:
                import traceback
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
                
                # Validate duck type and variant
                if not duck_config.get_duck_type(duck_type):
                    error_msg = f"Invalid duck type ({duck_type})"
                    self.logger.error(error_msg)
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
                    self.logger.error(error_msg)
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
                
                # Get internal name based on duck_type and variant
                internal_name = self.get_internal_duck_name(duck_type, variant)
                if not internal_name:
                    error_msg = f"Could not determine internal name for {duck_type}/{variant}"
                    self.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                    
                self.logger.debug(f"Mapped to internal duck name: {internal_name}")
                
                # Debug info
                debug_info = {
                    "url_path": request.path,
                    "duck_type": duck_type,
                    "variant": variant,
                    "internal_name": internal_name,
                    "request_args": dict(request.args)
                }
                
                # Check for testing files
                files = self.motion_service.list_testing_files(internal_name)
                self.logger.debug(f"Found testing files: {files}")
                
                return jsonify({
                    "success": True,
                    "files": files,
                    "debug_info": debug_info
                })
            except Exception as e:
                import traceback
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
                
                # Validate duck type and variant
                if not duck_config.get_duck_type(self.name):
                    error_msg = f"Invalid duck type ({self.name})"
                    self.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                
                if variant and not duck_config.get_variant(self.name, variant):
                    error_msg = f"Invalid variant ({variant}) for duck type ({self.name})"
                    self.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                
                # Get internal name
                internal_name = self.get_internal_duck_name(self.name, variant)
                if not internal_name:
                    error_msg = f"Could not determine internal name for {self.name}/{variant}"
                    self.logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'error': error_msg
                    }), 400
                
                self.logger.info(f"Downloading motion file for {self.name}/{variant} (internal: {internal_name})")
                
                # Find the latest motion file
                motion_files = self.motion_service.list_motion_files(internal_name)
                
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
                import traceback
                self.logger.error(f"Error downloading motion file: {str(e)}")
                self.logger.error(traceback.format_exc())
                return jsonify({
                    'success': False,
                    'error': f'Error downloading motion file: {str(e)}'
                }), 500

    def get_internal_duck_name(self, duck_type, variant=None):
        """Get the internal duck name based on the duck type and variant."""
        # Use the duck_config to get the internal name
        internal_name = duck_config.get_internal_name(duck_type, variant)
        
        # If no internal name found and variant is None, try to get the first variant
        if not internal_name and variant is None:
            duck_type_config = duck_config.get_duck_type(duck_type)
            if duck_type_config and 'variants' in duck_type_config:
                # Get first variant ID
                first_variant_id = next(iter(duck_type_config['variants'].keys()), None)
                if first_variant_id:
                    internal_name = duck_config.get_internal_name(duck_type, first_variant_id)
        
        self.logger.debug(f"Getting internal duck name for {duck_type}/{variant}: {internal_name}")
        return internal_name

# Create blueprint instance
duck = DuckBlueprint('duck', __name__) 
