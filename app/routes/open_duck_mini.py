from flask import Blueprint, request, jsonify, render_template, send_file
import subprocess
import os
from pathlib import Path
import json
import tempfile
from datetime import datetime
from ..services.training import training_service

# Create blueprint with URL prefix
open_duck_mini = Blueprint('open_duck_mini', __name__, url_prefix='/open_duck_mini')

def run_command(command, cwd):
    """
    Helper function to run a shell command in the given directory.
    Returns a tuple (stdout, stderr).
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

@open_duck_mini.route('/check_status')
def check_status():
    """
    Endpoint to check the status of Open Duck Mini running processes.
    """
    try:
        # Check if the playground is running
        running = check_process_running('gait_playground')
        
        return jsonify({
            'success': True,
            'running': running
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error checking status: {str(e)}'
        })

@open_duck_mini.route('/launch', methods=['POST'])
def launch():
    """
    Endpoint to launch the Open Duck Mini application.
    """
    try:
        # Launch the gait playground
        output = run_command(['uv', 'run', 'open_duck_reference_motion_generator/gait_playground.py', '--duck', 'open_duck_mini_v2'])
        
        return jsonify({
            'success': True,
            'output': output
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Launch failed with error: {str(e)}'
        })

@open_duck_mini.route('/generate_motion', methods=['POST'])
def generate_motion():
    """
    Endpoint to generate reference motions for the Open Duck Mini.
    Supports both Auto Waddle and Advanced modes.
    """
    try:
        # Get form data
        mode = request.form.get('mode', 'auto')
        output_dir = request.form.get('output_dir', 'generated_motions')
        num_jobs = request.form.get('num_jobs')
        
        # Build base command
        cmd = ['uv', 'run', 'scripts/auto_waddle.py']
        
        if num_jobs:
            cmd.append(f'-j{num_jobs}')
            
        if mode == 'auto':
            # Auto Waddle Mode
            generation_type = request.form.get('generation_type')
            cmd.append('--duck')
            cmd.append('open_duck_mini_v2')  # Default to v2 for auto mode
            
            if generation_type == 'sweep':
                cmd.append('--sweep')
            elif generation_type == 'random':
                num_motions = request.form.get('num_motions', '10')
                cmd.extend(['--num', num_motions])
            else:  # single motion
                motion_type = request.form.get('motion_type')
                duration = request.form.get('duration', '5')
                speed = request.form.get('speed', '0.5')
                cmd.extend(['--motion', motion_type, '--duration', duration, '--speed', speed])
        else:
            # Advanced Mode
            duck_type = request.form.get('duck_type', 'open_duck_mini_v2')
            cmd.append('--duck')
            cmd.append(duck_type)
            
            # Handle sweep parameters if provided
            speed_min = request.form.get('speed_min')
            speed_max = request.form.get('speed_max')
            duration_min = request.form.get('duration_min')
            duration_max = request.form.get('duration_max')
            
            if all([speed_min, speed_max, duration_min, duration_max]):
                cmd.append('--sweep')
                # These parameters will be used by the script to define the sweep range
                cmd.extend([
                    '--speed_min', speed_min,
                    '--speed_max', speed_max,
                    '--duration_min', duration_min,
                    '--duration_max', duration_max
                ])
            
        cmd.extend(['--output_dir', output_dir])
        
        # Run command
        stdout, stderr = run_command(cmd)
        
        # Read generated motion data
        motion_file = os.path.join(output_dir, 'motion.json')
        if os.path.exists(motion_file):
            with open(motion_file, 'r') as f:
                motion_data = json.load(f)
        else:
            motion_data = None
        
        return jsonify({
            'success': True,
            'output': stdout,
            'error': stderr,
            'motion_data': motion_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Motion generation failed with error: {str(e)}'
        })

@open_duck_mini.route('/download_motion', methods=['POST'])
def download_motion():
    """
    Endpoint to download a generated motion file.
    """
    try:
        motion_data = request.json
        if not motion_data:
            return jsonify({
                'success': False,
                'error': 'No motion data provided'
            })
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(motion_data, temp_file)
            temp_path = temp_file.name
        
        # Send the file
        return send_file(
            temp_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'motion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Download failed with error: {str(e)}'
        })
    finally:
        # Clean up the temporary file
        if 'temp_path' in locals():
            try:
                os.unlink(temp_path)
            except:
                pass

@open_duck_mini.route('/start_training', methods=['POST'])
def start_training():
    """
    Endpoint to start training for the Open Duck Mini.
    """
    try:
        # Get training options from form data
        training_options = {
            'model_type': request.form.get('model_type'),
            'num_steps': request.form.get('num_steps'),
            'learning_rate': request.form.get('learning_rate')
        }
        
        # Start training
        success, result = training_service.start_training('open_duck_mini_v2', training_options)
        
        if not success:
            return jsonify({
                'success': False,
                'error': result
            }), 400
            
        return jsonify({
            'success': True,
            'task_id': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Training failed to start: {str(e)}'
        }), 500

@open_duck_mini.route('/training_status/<task_id>', methods=['GET'])
def training_status(task_id):
    """
    Endpoint to check the status of a training task.
    """
    try:
        status = training_service.get_task_status(task_id)
        
        if status is None:
            return jsonify({
                'success': False,
                'error': 'Task not found'
            }), 404
            
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get training status: {str(e)}'
        }), 500

@open_duck_mini.route('/start_testing', methods=['POST'])
def start_testing():
    """
    Endpoint to start testing for the Open Duck Mini.
    """
    try:
        # Get testing options from request
        testing_options = request.form.to_dict()
        
        # Build testing command
        cmd = ['uv', 'run', 'scripts/test_model.py']
        cmd.extend(['--duck', 'open_duck_mini_v2'])
        
        if testing_options.get('test_episodes'):
            cmd.extend(['--episodes', testing_options['test_episodes']])
        
        if testing_options.get('test_model'):
            cmd.extend(['--model', testing_options['test_model']])
        
        # Run command
        stdout, stderr = run_command(cmd)
        
        # Parse results from stdout
        results = {
            'average_reward': 0.0,
            'success_rate': 0.0
        }
        
        # Try to extract results from stdout
        for line in stdout.split('\n'):
            if 'Average Reward:' in line:
                try:
                    results['average_reward'] = float(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    pass
            elif 'Success Rate:' in line:
                try:
                    results['success_rate'] = float(line.split(':')[1].strip().rstrip('%'))
                except (ValueError, IndexError):
                    pass
        
        # If we got any errors, include them in the response
        if stderr:
            return jsonify({
                'success': True,
                'results': results,
                'output': stdout,
                'error': stderr,
                'warning': 'Some errors occurred during testing'
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'output': stdout
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Testing failed: {str(e)}',
            'details': str(e.__class__.__name__)
        }), 500 
