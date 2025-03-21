from flask import Blueprint, request, jsonify, current_app
from pathlib import Path
from ..services.open_duck_mini_playground import OpenDuckPlaygroundService
from ..services.awd import AWDService
from ..services.deployment import DeploymentService
from ..services.reference_motion_generation import ReferenceMotionGenerationService

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
        
    def register_routes(self):
        """Register all routes for the application."""
        
        # Training routes
        @self.app.route('/api/train', methods=['POST'])
        def start_training():
            try:
                data = request.get_json()
                duck_type = data.get('duck_type')
                num_envs = data.get('num_envs', 1)
                motion_file = data.get('motion_file')
                framework = data.get('framework', 'playground')  # or 'awd'
                
                if framework == 'playground':
                    success, message, output = self.playground_service.train_model(
                        duck_type=duck_type,
                        num_envs=num_envs,
                        motion_file=motion_file
                    )
                else:
                    success, message, output = self.awd_service.train_model(
                        duck_type=duck_type,
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
                
        # Motion generation routes
        @self.app.route('/api/generate_motion', methods=['POST'])
        def generate_motion():
            try:
                data = request.get_json()
                duck_type = data.get('duck_type')
                mode = data.get('mode', 'auto')
                params = data.get('params', {})
                
                success, message, output = self.motion_service.generate_motion(
                    duck_type=duck_type,
                    mode=mode,
                    **params
                )
                
                return jsonify({
                    'success': success,
                    'message': message,
                    'output': output
                })
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error generating motion: {str(e)}'
                })
                
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