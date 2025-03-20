from flask import Blueprint, request, jsonify, render_template, send_file, current_app, url_for
import subprocess
import os
from pathlib import Path
import json
import tempfile
from datetime import datetime
from ..services.training import training_service
import glob
import shutil
import time

# Create blueprint with URL prefix
open_duck_mini = Blueprint('open_duck_mini', __name__, url_prefix='/open_duck_mini')

def run_command(command, cwd):
    """
    Helper function to run a shell command in the given directory.
    Returns a tuple (stdout, stderr).
    """
    try:
        # If command is a list, join it with spaces
        if isinstance(command, list):
            command = ' '.join(command)
            
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True  # Raise exception if command fails
        )
        return result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        # Only return the error message once
        return e.stdout, e.stderr
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
        output = run_command(['uv', 'run', '--active', 'submodules/open_duck_reference_motion_generator/open_duck_reference_motion_generator/gait_playground.py', '--duck', 'open_duck_mini_v2'])
        
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
        
        # Set up paths
        repo_root = Path(__file__).parent.parent.parent
        submodule_dir = repo_root / 'submodules/open_duck_reference_motion_generator'
        output_dir = repo_root / 'generated_motions'
        output_dir.mkdir(exist_ok=True)
        
        # Create unique run ID based on timestamp
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Create a temporary directory for this specific run
        with tempfile.TemporaryDirectory(prefix=f'motion_gen_{run_id}_') as temp_dir:
            temp_dir_path = Path(temp_dir)
            
            # Create subdirectories that might be needed
            (temp_dir_path / 'log').mkdir(exist_ok=True)
            (temp_dir_path / 'tmp').mkdir(exist_ok=True)
            
            if mode == 'auto':
                # Auto Waddle Mode
                generation_type = request.form.get('generation_type')
                cmd = ['uv', 'run', '--active', 'scripts/auto_waddle.py']
                cmd.append('--duck')
                cmd.append('open_duck_mini_v2')  # Default to v2 for auto mode
                
                if generation_type == 'sweep':
                    cmd.append('--sweep')
                elif generation_type == 'random':
                    num_motions = request.form.get('num_motions', '10')
                    cmd.extend(['--num', num_motions])
                else:  # single motion
                    cmd.extend(['--num', '1'])
                    
            else:
                # Advanced Mode - Use gait_generator.py
                cmd = ['uv', 'run', '--active', 'open_duck_reference_motion_generator/gait_generator.py']
                cmd.extend(['--duck', 'open_duck_mini_v2'])
                cmd.extend(['--name', f'motion_{run_id}'])
                
                # Add all the advanced parameters
                advanced_params = {
                    'dx': request.form.get('dx'),
                    'dy': request.form.get('dy'),
                    'dtheta': request.form.get('dtheta'),
                    'walk_com_height': request.form.get('walk_com_height'),
                    'walk_foot_height': request.form.get('walk_foot_height'),
                    'walk_trunk_pitch': request.form.get('walk_trunk_pitch'),
                    'walk_foot_rise_ratio': request.form.get('walk_foot_rise_ratio'),
                    'single_support_duration': request.form.get('single_support_duration'),
                    'feet_spacing': request.form.get('feet_spacing'),
                    'zmp_margin': request.form.get('zmp_margin'),
                    'length': request.form.get('duration', '5')
                }
                
                # Only add parameters that were provided
                for param, value in advanced_params.items():
                    if value is not None:
                        cmd.extend([f'--{param}', str(value)])
            
            # Add output directory to both modes
            cmd.extend(['--output_dir', str(temp_dir_path)])
            
            # Step 1: Generate motions
            stdout, stderr = run_command(cmd, cwd=str(submodule_dir))
            
            # Log the command output
            log_output = []
            if stdout:
                log_output.append("Command Output:")
                log_output.extend(stdout.split('\n'))
            
            # Only treat package installation messages as warnings, not errors
            if stderr:
                if "Failed to uninstall package" in stderr or "Installed" in stderr:
                    log_output.append("\nPackage Installation Messages:")
                    log_output.extend(stderr.split('\n'))
                else:
                    # If there are actual errors, include them
                    log_output.append("\nErrors:")
                    log_output.extend(stderr.split('\n'))
            
            # Wait a bit and check for motion files in the temp directory
            max_wait = 10  # Maximum wait time in seconds
            wait_interval = 0.5  # Check every half second
            waited = 0
            
            while waited < max_wait:
                # Only check temp directory since we're using a unique one
                motion_files = list(temp_dir_path.glob('*.json'))
                if motion_files:
                    break
                    
                time.sleep(wait_interval)
                waited += wait_interval
            
            if not motion_files:
                return jsonify({
                    'success': False,
                    'error': 'No motion files were generated after waiting',
                    'output': '\n'.join(log_output)
                })
            
            # Step 2: Fit polynomials to the generated motions
            fit_cmd = ['uv', 'run', '--active', 'scripts/fit_poly.py', '--ref_motion'] + [str(f) for f in motion_files]
            fit_stdout, fit_stderr = run_command(fit_cmd, cwd=str(submodule_dir))
            
            # Add polynomial fitting output to logs
            if fit_stdout:
                log_output.append("\nPolynomial Fitting Output:")
                log_output.extend(fit_stdout.split('\n'))
            if fit_stderr and not ("Uninstalled" in fit_stderr or "Installed" in fit_stderr):
                log_output.append("\nPolynomial Fitting Errors:")
                log_output.extend(fit_stderr.split('\n'))
            
            # Wait and check for polynomial coefficients file
            waited = 0
            pkl_file = None
            while waited < max_wait:
                # Check in temp directory and submodule directory
                possible_pkl_locations = [
                    temp_dir_path / 'polynomial_coefficients.pkl',
                    submodule_dir / 'polynomial_coefficients.pkl'
                ]
                
                for loc in possible_pkl_locations:
                    if loc.exists():
                        pkl_file = loc
                        break
                
                if pkl_file:
                    break
                    
                time.sleep(wait_interval)
                waited += wait_interval
            
            if not pkl_file:
                return jsonify({
                    'success': False,
                    'error': 'Polynomial coefficients file not found after waiting',
                    'output': '\n'.join(log_output)
                })
            
            # Step 3: Copy files to final locations
            try:
                # Create run-specific directory in output_dir
                run_output_dir = output_dir / run_id
                run_output_dir.mkdir(exist_ok=True)
                
                # Copy motion files to output directory
                for motion_file in motion_files:
                    shutil.copy2(motion_file, run_output_dir / motion_file.name)
                
                # Copy polynomial coefficients
                shutil.copy2(pkl_file, run_output_dir / pkl_file.name)
                
                # Copy to playground directory
                playground_pkl_path = repo_root / 'submodules/open_duck_playground/playground/open_duck_mini_v2/data' / pkl_file.name
                playground_pkl_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pkl_file, playground_pkl_path)
                
                # Create a symlink to the latest run
                latest_link = output_dir / 'latest'
                if latest_link.exists():
                    latest_link.unlink()
                latest_link.symlink_to(run_output_dir, target_is_directory=True)
                
            except Exception as e:
                log_output.append(f"\nWarning: Error copying files: {str(e)}")
            
            # Read generated motion data for preview
            try:
                motion_file = run_output_dir / motion_files[0].name
                if motion_file.exists():
                    with open(motion_file, 'r') as f:
                        motion_data = json.load(f)
                else:
                    motion_data = None
            except Exception as e:
                log_output.append(f"\nWarning: Error reading motion data: {str(e)}")
                motion_data = None
            
            return jsonify({
                'success': True,
                'output': '\n'.join(log_output),
                'motion_data': motion_data,
                'run_id': run_id,
                'steps_completed': [
                    'Generated reference motions',
                    'Fitted polynomials',
                    'Generated polynomial coefficients',
                    'Copied coefficients to required locations'
                ]
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Motion generation failed with error: {str(e)}',
            'output': str(e)
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
        cmd = ['uv', 'run', '--active', 'scripts/test_model.py']
        cmd.extend(['--duck', 'open_duck_mini_v2'])
        
        if testing_options.get('test_episodes'):
            cmd.extend(['--episodes', testing_options['test_episodes']])
        
        if testing_options.get('test_model'):
            cmd.extend(['--model', testing_options['test_model']])
        
        # Run command
        stdout, stderr = run_command(cmd, cwd=str(Path(__file__).parent.parent.parent))
        
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

@open_duck_mini.route('/launch_playground', methods=['POST'])
def launch_playground():
    """
    Endpoint to launch the gait playground for visualization.
    """
    try:
        # Get duck type from request
        duck_type = request.form.get('duck_type', 'open_duck_mini_v2')
        
        # Set the working directory to the submodule
        submodule_dir = str(Path(__file__).parent.parent.parent / 'submodules/open_duck_reference_motion_generator')
        
        # Launch the gait playground
        cmd = ['uv', 'run', '--active', 'open_duck_reference_motion_generator/gait_playground.py', '--duck', duck_type]
        stdout, stderr = run_command(cmd, cwd=submodule_dir)
        
        if stderr:
            return jsonify({
                'success': False,
                'error': stderr,
                'output': stdout
            })
            
        return jsonify({
            'success': True,
            'output': stdout
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to launch playground: {str(e)}'
        })

@open_duck_mini.route('/fit_polynomials', methods=['POST'])
def fit_polynomials():
    try:
        # Get the latest generated motion file
        repo_root = Path(__file__).parent.parent.parent
        motion_dir = repo_root / 'generated_motions'
        motion_files = list(motion_dir.glob('*.json'))
        
        if not motion_files:
            return jsonify({'success': False, 'error': 'No motion files found'})
        
        latest_motion = max(motion_files, key=lambda p: p.stat().st_mtime)
        
        # Run the polynomial fitting script
        submodule_dir = repo_root / 'submodules/open_duck_reference_motion_generator'
        cmd = [
            'uv', 'run', '--active', 'scripts/fit_poly.py',
            '--ref_motion', str(latest_motion)
        ]
        
        stdout, stderr = run_command(cmd, cwd=str(submodule_dir))
        
        if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
            return jsonify({'success': False, 'error': stderr})
        
        # Generate the plot
        plot_cmd = [
            'uv', 'run', '--active', 'scripts/plot_poly_fit.py',
            '--coefficients', 'polynomial_coefficients.pkl'
        ]
        
        plot_stdout, plot_stderr = run_command(plot_cmd, cwd=str(submodule_dir))
        
        if plot_stderr and not ("Uninstalled" in plot_stderr or "Installed" in plot_stderr):
            return jsonify({'success': False, 'error': plot_stderr})
        
        # Save the plot to a static file
        static_dir = repo_root / 'app/static/plots'
        static_dir.mkdir(parents=True, exist_ok=True)
        plot_path = static_dir / 'polynomial_fit.png'
        
        if (submodule_dir / 'polynomial_fit.png').exists():
            shutil.copy2(submodule_dir / 'polynomial_fit.png', plot_path)
        
        return jsonify({
            'success': True,
            'plot_url': url_for('static', filename='plots/polynomial_fit.png')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@open_duck_mini.route('/replay_motion', methods=['POST'])
def replay_motion():
    try:
        # Get the latest generated motion file
        repo_root = Path(__file__).parent.parent.parent
        motion_dir = repo_root / 'generated_motions'
        motion_files = list(motion_dir.glob('*.json'))
        
        if not motion_files:
            return jsonify({'success': False, 'error': 'No motion files found'})
        
        latest_motion = max(motion_files, key=lambda p: p.stat().st_mtime)
        
        # Run the replay script
        submodule_dir = repo_root / 'submodules/open_duck_reference_motion_generator'
        cmd = [
            'uv', 'run', '--active', 'scripts/replay_motion.py',
            '-f', str(latest_motion)
        ]
        
        # Start the replay process in the background
        process = subprocess.Popen(cmd, cwd=str(submodule_dir))
        
        return jsonify({
            'success': True,
            'message': 'Motion replay started'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 
