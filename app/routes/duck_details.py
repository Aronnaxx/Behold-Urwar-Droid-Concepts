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
import matplotlib.pyplot as plt
import numpy as np
import sys

class DuckDetailsBlueprint(Blueprint):
    """Base class for duck-specific routes and functionality."""
    
    def __init__(self, name, import_name, url_prefix, duck_type):
        super().__init__(name, import_name, url_prefix=url_prefix)
        self.duck_type = duck_type
        self._playground_process = None
        
    def run_command(self, command, cwd):
        """Helper function to run a shell command in the given directory."""
        try:
            if isinstance(command, list):
                command = ' '.join(command)
                
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.stdout, e.stderr
        except Exception as e:
            return "", str(e)

    def check_process_running(self, process_name):
        """Check if a process is running."""
        try:
            output = subprocess.check_output(['pgrep', '-f', process_name])
            return bool(output)
        except subprocess.CalledProcessError:
            return False

    def register_routes(self):
        """Register all routes for this duck type."""
        self.add_url_rule('/check_status', 'check_status', self.check_status)
        self.add_url_rule('/launch', 'launch', self.launch, methods=['POST'])
        self.add_url_rule('/generate_motion', 'generate_motion', self.generate_motion, methods=['POST'])
        self.add_url_rule('/download_motion', 'download_motion', self.download_motion, methods=['POST'])
        self.add_url_rule('/start_training', 'start_training', self.start_training, methods=['POST'])
        self.add_url_rule('/training_status/<task_id>', 'training_status', self.training_status)
        self.add_url_rule('/start_testing', 'start_testing', self.start_testing, methods=['POST'])
        self.add_url_rule('/launch_playground', 'launch_playground', self.launch_playground, methods=['POST'])
        self.add_url_rule('/close_playground', 'close_playground', self.close_playground, methods=['POST'])
        self.add_url_rule('/fit_polynomials', 'fit_polynomials', self.fit_polynomials, methods=['POST'])
        self.add_url_rule('/replay_motion', 'replay_motion', self.replay_motion, methods=['POST'])
        self.add_url_rule('/plot_polynomials', 'plot_polynomials', self.plot_polynomials, methods=['POST'])

    def check_status(self):
        """Check the status of running processes."""
        try:
            running = self.check_process_running('gait_playground')
            return jsonify({
                'success': True,
                'running': running
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Error checking status: {str(e)}'
            })

    def launch(self):
        """Launch the duck application."""
        try:
            output = self.run_command(['uv', 'run', '--active', 'submodules/open_duck_reference_motion_generator/open_duck_reference_motion_generator/gait_playground.py', '--duck', self.duck_type])
            return jsonify({
                'success': True,
                'output': output
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Launch failed with error: {str(e)}'
            })

    def generate_motion(self):
        """Generate reference motions for the duck."""
        try:
            mode = request.form.get('mode', 'auto')
            repo_root = Path(__file__).parent.parent.parent
            submodule_dir = repo_root / 'submodules/open_duck_reference_motion_generator'
            output_dir = repo_root / 'generated_motions' / self.duck_type
            output_dir.mkdir(parents=True, exist_ok=True)
            
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            with tempfile.TemporaryDirectory(prefix=f'motion_gen_{run_id}_') as temp_dir:
                temp_dir_path = Path(temp_dir)
                (temp_dir_path / 'log').mkdir(exist_ok=True)
                (temp_dir_path / 'tmp').mkdir(exist_ok=True)
                
                if mode == 'auto':
                    generation_type = request.form.get('generation_type')
                    cmd = ['uv', 'run', '--active', 'scripts/auto_waddle.py']
                    cmd.extend(['--duck', self.duck_type])
                    
                    if generation_type == 'sweep':
                        cmd.append('--sweep')
                    elif generation_type == 'random':
                        num_motions = request.form.get('num_motions', '10')
                        cmd.extend(['--num', num_motions])
                    else:  # single motion
                        cmd.extend(['--num', '1'])
                else:
                    cmd = ['uv', 'run', '--active', 'open_duck_reference_motion_generator/gait_generator.py']
                    cmd.extend(['--duck', self.duck_type])
                    cmd.extend(['--name', f'motion_{run_id}'])
                    
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
                    
                    for param, value in advanced_params.items():
                        if value is not None:
                            cmd.extend([f'--{param}', str(value)])
                
                cmd.extend(['--output_dir', str(temp_dir_path)])
                
                stdout, stderr = self.run_command(cmd, cwd=str(submodule_dir))
                
                log_output = []
                if stdout:
                    log_output.append("Command Output:")
                    log_output.extend(stdout.split('\n'))
                
                if stderr:
                    if "Failed to uninstall package" in stderr or "Installed" in stderr:
                        log_output.append("\nPackage Installation Messages:")
                        log_output.extend(stderr.split('\n'))
                    else:
                        log_output.append("\nErrors:")
                        log_output.extend(stderr.split('\n'))
                
                max_wait = 30
                wait_interval = 0.5
                waited = 0
                
                while waited < max_wait:
                    motion_files = list(temp_dir_path.glob('*.json'))
                    if motion_files:
                        break
                    time.sleep(wait_interval)
                    waited += wait_interval
                
                if not motion_files:
                    return jsonify({
                        'success': False,
                        'error': 'No motion files were generated after waiting 30s',
                        'output': '\n'.join(log_output)
                    })
                
                fit_cmd = ['uv', 'run', '--active', 'scripts/fit_poly.py', '--ref_motion'] + [str(f) for f in motion_files]
                fit_stdout, fit_stderr = self.run_command(fit_cmd, cwd=str(submodule_dir))
                
                if fit_stdout:
                    log_output.append("\nPolynomial Fitting Output:")
                    log_output.extend(fit_stdout.split('\n'))
                if fit_stderr and not ("Uninstalled" in fit_stderr or "Installed" in fit_stderr):
                    log_output.append("\nPolynomial Fitting Errors:")
                    log_output.extend(fit_stderr.split('\n'))
                
                waited = 0
                pkl_file = None
                while waited < max_wait:
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
                        'error': 'No polynomial coefficients file was generated after waiting 30s',
                        'output': '\n'.join(log_output)
                    })
                
                # Create a run-specific directory in the duck's output directory
                run_output_dir = output_dir / run_id
                run_output_dir.mkdir(exist_ok=True)
                
                # Move all generated files to the run-specific directory
                for file in motion_files:
                    shutil.copy2(file, run_output_dir / file.name)
                shutil.copy2(pkl_file, run_output_dir / pkl_file.name)
                
                # Update the latest symlink for this duck type
                latest_link = repo_root / 'generated_motions' / f'latest_{self.duck_type}'
                if latest_link.exists():
                    latest_link.unlink()
                latest_link.symlink_to(run_output_dir, target_is_directory=True)
                
                # Copy files to the playground submodule
                try:
                    playground_pkl_path = repo_root / 'submodules/open_duck_playground/playground' / self.duck_type / 'data' / pkl_file.name
                    playground_pkl_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(pkl_file, playground_pkl_path)
                except Exception as e:
                    log_output.append(f"\nWarning: Error copying files to playground: {str(e)}")
                
                return jsonify({
                    'success': True,
                    'output': '\n'.join(log_output),
                    'files': [str(f.name) for f in motion_files]
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Motion generation failed: {str(e)}',
                'output': str(e)
            })

    def download_motion(self):
        """Download a generated motion file."""
        try:
            repo_root = Path(__file__).parent.parent.parent
            latest_dir = repo_root / 'generated_motions' / f'latest_{self.duck_type}'
            
            if not latest_dir.exists() or not latest_dir.is_symlink():
                return jsonify({
                    'success': False,
                    'error': f'No recent motion generation found for {self.duck_type}'
                })
            
            motion_files = list(latest_dir.glob('*.json'))
            if not motion_files:
                return jsonify({
                    'success': False,
                    'error': 'No motion files found in latest run'
                })
            
            # Read the motion file
            with open(motion_files[0], 'r') as f:
                motion_data = json.load(f)
            
            # Create a temporary file with the motion data
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(motion_data, temp_file)
                temp_path = temp_file.name
            
            return send_file(
                temp_path,
                mimetype='application/json',
                as_attachment=True,
                download_name=f'motion_{self.duck_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Download failed with error: {str(e)}'
            })
        finally:
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass

    def start_training(self):
        """Start training for the duck."""
        try:
            training_options = {
                'model_type': request.form.get('model_type'),
                'num_steps': request.form.get('num_steps'),
                'learning_rate': request.form.get('learning_rate')
            }
            
            success, result = training_service.start_training(self.duck_type, training_options)
            
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

    def training_status(self, task_id):
        """Check the status of a training task."""
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

    def start_testing(self):
        """Start testing for the duck."""
        try:
            testing_options = request.form.to_dict()
            
            cmd = ['uv', 'run', '--active', 'scripts/test_model.py']
            cmd.extend(['--duck', self.duck_type])
            
            if testing_options.get('test_episodes'):
                cmd.extend(['--episodes', testing_options['test_episodes']])
            
            if testing_options.get('test_model'):
                cmd.extend(['--model', testing_options['test_model']])
            
            stdout, stderr = self.run_command(cmd, cwd=str(Path(__file__).parent.parent.parent))
            
            results = {
                'average_reward': 0.0,
                'success_rate': 0.0
            }
            
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

    def launch_playground(self):
        """Launch the gait playground for visualization."""
        try:
            if self._playground_process is not None and self._playground_process.poll() is None:
                return jsonify({
                    'success': True,
                    'message': 'Playground is already running'
                })

            repo_root = Path(os.getcwd())
            submodule_path = repo_root / 'submodules/open_duck_reference_motion_generator'
                
            os.chdir(submodule_path)
            
            cmd = [sys.executable, 'open_duck_reference_motion_generator/gait_playground.py', '--duck', self.duck_type]
            self._playground_process = subprocess.Popen(cmd, env=os.environ.copy())
            
            time.sleep(1)
            
            return jsonify({
                'success': True,
                'message': 'Playground launched successfully'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Failed to launch playground: {str(e)}'
            })

    def close_playground(self):
        """Close the gait playground."""
        try:
            if self._playground_process is not None:
                self._playground_process.terminate()
                try:
                    self._playground_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._playground_process.kill()
                    self._playground_process.wait()
                
                self._playground_process = None
                
            return jsonify({
                'success': True,
                'message': 'Playground closed successfully'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    def fit_polynomials(self):
        """Fit polynomials to the generated motions."""
        try:
            repo_root = Path(__file__).parent.parent.parent
            latest_dir = repo_root / 'generated_motions' / f'latest_{self.duck_type}'
            
            if not latest_dir.exists() or not latest_dir.is_symlink():
                return jsonify({'success': False, 'error': f'No recent motion generation found for {self.duck_type}'})
                
            motion_files = list(latest_dir.glob('*.json'))
            if not motion_files:
                return jsonify({'success': False, 'error': 'No motion files found in latest run'})
            
            submodule_dir = repo_root / 'submodules/open_duck_reference_motion_generator'
            cmd = [
                'uv', 'run', '--active', 'scripts/fit_poly.py',
                '--ref_motion', str(motion_files[0])
            ]
            
            stdout, stderr = self.run_command(cmd, cwd=str(submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return jsonify({'success': False, 'error': stderr})
            
            plot_cmd = [
                'uv', 'run', '--active', 'scripts/plot_poly_fit.py',
                '--coefficients', 'polynomial_coefficients.pkl'
            ]
            
            plot_stdout, plot_stderr = self.run_command(plot_cmd, cwd=str(submodule_dir))
            
            if plot_stderr and not ("Uninstalled" in plot_stderr or "Installed" in plot_stderr):
                return jsonify({'success': False, 'error': plot_stderr})
            
            static_dir = repo_root / 'app/static/plots'
            static_dir.mkdir(parents=True, exist_ok=True)
            plot_path = static_dir / f'polynomial_fit_{self.duck_type}.png'
            
            if (submodule_dir / 'polynomial_fit.png').exists():
                shutil.copy2(submodule_dir / 'polynomial_fit.png', plot_path)
            
            return jsonify({
                'success': True,
                'plot_url': url_for('static', filename=f'plots/polynomial_fit_{self.duck_type}.png')
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    def replay_motion(self):
        """Replay a generated motion."""
        try:
            repo_root = Path(__file__).parent.parent.parent
            latest_dir = repo_root / 'generated_motions' / f'latest_{self.duck_type}'
            
            if not latest_dir.exists() or not latest_dir.is_symlink():
                return jsonify({'success': False, 'error': f'No recent motion generation found for {self.duck_type}'})
                
            motion_files = list(latest_dir.glob('*.json'))
            if not motion_files:
                return jsonify({'success': False, 'error': 'No motion files found in latest run'})
            
            submodule_dir = repo_root / 'submodules/open_duck_reference_motion_generator'
            cmd = [
                'uv', 'run', '--active', 'scripts/replay_motion.py',
                '-f', str(motion_files[0])
            ]
            
            process = subprocess.Popen(cmd, cwd=str(submodule_dir))
            
            return jsonify({
                'success': True,
                'message': 'Motion replay started'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    def plot_polynomials(self):
        """Plot polynomial trajectories."""
        try:
            repo_root = Path(os.getcwd())
            latest_dir = repo_root / 'generated_motions/latest'
            
            if not latest_dir.exists() or not latest_dir.is_symlink():
                return jsonify({'success': False, 'error': 'No recent motion generation found'})
                
            poly_files = list(latest_dir.glob('*.poly'))
            if not poly_files:
                return jsonify({'success': False, 'error': 'No polynomial files found'})
                
            plots_dir = repo_root / 'static/plots'
            plots_dir.mkdir(parents=True, exist_ok=True)
            
            plt.figure(figsize=(12, 8))
            
            for poly_file in poly_files:
                joint_name = poly_file.stem
                coeffs = np.loadtxt(poly_file)
                
                x = np.linspace(0, 1, 100)
                y = np.polyval(coeffs[::-1], x)
                
                plt.plot(x, y, label=joint_name)
            
            plt.title('Joint Trajectories')
            plt.xlabel('Normalized Time')
            plt.ylabel('Joint Angle (rad)')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.grid(True)
            
            plot_path = plots_dir / 'trajectories.png'
            plt.savefig(plot_path, bbox_inches='tight')
            plt.close()
            
            return jsonify({
                'success': True,
                'plot_url': '/static/plots/trajectories.png'
            })
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

# Create specific duck implementations
open_duck_mini = DuckDetailsBlueprint('open_duck_mini', __name__, url_prefix='/open_duck_mini_v2', duck_type='open_duck_mini_v2')
bdx = DuckDetailsBlueprint('bdx', __name__, url_prefix='/go_bdx', duck_type='go_bdx')

# Register routes for each implementation
open_duck_mini.register_routes()
bdx.register_routes() 
