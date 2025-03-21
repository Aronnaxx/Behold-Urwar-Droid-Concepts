import subprocess
import os
from pathlib import Path
import shutil
import time
import json
from typing import Tuple, Optional, List, Dict
import tempfile
from datetime import datetime

class ReferenceMotionGenerationService:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.submodule_dir = workspace_root / 'submodules/open_duck_reference_motion_generator'
        
    def run_command(self, command: List[str], cwd: str) -> Tuple[str, str]:
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

    def generate_motion(self, 
                       duck_type: str, 
                       mode: str = 'auto',
                       **params) -> Tuple[bool, str, Optional[Dict]]:
        """Generate reference motions for the duck."""
        try:
            output_dir = self.workspace_root / 'generated_motions' / duck_type
            output_dir.mkdir(parents=True, exist_ok=True)
            
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            
            with tempfile.TemporaryDirectory(prefix=f'motion_gen_{run_id}_') as temp_dir:
                temp_dir_path = Path(temp_dir)
                (temp_dir_path / 'log').mkdir(exist_ok=True)
                (temp_dir_path / 'tmp').mkdir(exist_ok=True)
                
                if mode == 'auto':
                    generation_type = params.get('generation_type')
                    cmd = ['uv', 'run', '--active', 'scripts/auto_waddle.py']
                    cmd.extend(['--duck', duck_type])
                    
                    if generation_type == 'sweep':
                        cmd.append('--sweep')
                    elif generation_type == 'random':
                        num_motions = params.get('num_motions', '10')
                        cmd.extend(['--num', num_motions])
                    else:  # single motion
                        cmd.extend(['--num', '1'])
                else:
                    cmd = ['uv', 'run', '--active', 'open_duck_reference_motion_generator/gait_generator.py']
                    cmd.extend(['--duck', duck_type])
                    cmd.extend(['--name', f'motion_{run_id}'])
                    
                    advanced_params = {
                        'dx': params.get('dx'),
                        'dy': params.get('dy'),
                        'dtheta': params.get('dtheta'),
                        'walk_com_height': params.get('walk_com_height'),
                        'walk_foot_height': params.get('walk_foot_height'),
                        'walk_trunk_pitch': params.get('walk_trunk_pitch'),
                        'walk_foot_rise_ratio': params.get('walk_foot_rise_ratio'),
                        'single_support_duration': params.get('single_support_duration'),
                        'feet_spacing': params.get('feet_spacing'),
                        'zmp_margin': params.get('zmp_margin'),
                        'length': params.get('duration', '5')
                    }
                    
                    for param_name, value in advanced_params.items():
                        if value is not None:
                            cmd.extend([f'--{param_name}', str(value)])
                
                cmd.extend(['--output_dir', str(temp_dir_path)])
                
                stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
                
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
                
                # Wait for motion files to be generated
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
                    return False, "No motion files were generated after waiting 30s", {
                        'output': '\n'.join(log_output)
                    }
                
                # Fit polynomials
                fit_cmd = ['uv', 'run', '--active', 'scripts/fit_poly.py', '--ref_motion'] + [str(f) for f in motion_files]
                fit_stdout, fit_stderr = self.run_command(fit_cmd, str(self.submodule_dir))
                
                if fit_stdout:
                    log_output.append("\nPolynomial Fitting Output:")
                    log_output.extend(fit_stdout.split('\n'))
                if fit_stderr and not ("Uninstalled" in fit_stderr or "Installed" in fit_stderr):
                    log_output.append("\nPolynomial Fitting Errors:")
                    log_output.extend(fit_stderr.split('\n'))
                
                # Wait for polynomial coefficients file
                waited = 0
                pkl_file = None
                while waited < max_wait:
                    possible_pkl_locations = [
                        temp_dir_path / 'polynomial_coefficients.pkl',
                        self.submodule_dir / 'polynomial_coefficients.pkl'
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
                    return False, "No polynomial coefficients file was generated after waiting 30s", {
                        'output': '\n'.join(log_output)
                    }
                
                # Create run-specific output directory
                run_output_dir = output_dir / run_id
                run_output_dir.mkdir(exist_ok=True)
                
                # Copy generated files
                for file in motion_files:
                    shutil.copy2(file, run_output_dir / file.name)
                shutil.copy2(pkl_file, run_output_dir / pkl_file.name)
                
                # Update latest symlink
                latest_link = self.workspace_root / 'generated_motions' / f'latest_{duck_type}'
                if latest_link.exists():
                    latest_link.unlink()
                latest_link.symlink_to(run_output_dir, target_is_directory=True)
                
                # Copy to playground if needed
                try:
                    playground_pkl_path = self.workspace_root / 'submodules/open_duck_playground/playground' / duck_type / 'data' / pkl_file.name
                    playground_pkl_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(pkl_file, playground_pkl_path)
                except Exception as e:
                    log_output.append(f"\nWarning: Error copying files to playground: {str(e)}")
                
                return True, "Motion generation completed successfully", {
                    'output': '\n'.join(log_output),
                    'files': [str(f.name) for f in motion_files],
                    'run_id': run_id
                }
                
        except Exception as e:
            return False, f"Motion generation failed: {str(e)}", None

    def fit_polynomials(self, motion_files: List[str]) -> Tuple[bool, str, Optional[str]]:
        """Fit polynomials to reference motion data."""
        try:
            cmd = ['uv', 'run', '--active', 'scripts/fit_poly.py', '--ref_motion'] + motion_files
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "Polynomial fitting failed", stderr
                
            return True, "Polynomial fitting completed successfully", stdout
            
        except Exception as e:
            return False, f"Error fitting polynomials: {str(e)}", None

    def replay_motion(self, motion_file: str) -> Tuple[bool, str, Optional[str]]:
        """Replay a reference motion."""
        try:
            cmd = ['uv', 'run', '--active', 'scripts/replay_motion.py', '--motion_file', motion_file]
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "Motion replay failed", stderr
                
            return True, "Motion replay started successfully", stdout
            
        except Exception as e:
            return False, f"Error replaying motion: {str(e)}", None

    def plot_polynomials(self, pkl_file: str, output_dir: str) -> Tuple[bool, str, Optional[Dict]]:
        """Plot polynomial coefficients."""
        try:
            cmd = ['uv', 'run', '--active', 'scripts/plot_polynomials.py', '--pkl_file', pkl_file, '--output_dir', output_dir]
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "Polynomial plotting failed", None
                
            # Get list of generated plot files
            plot_files = []
            output_path = Path(output_dir)
            for plot_file in output_path.glob('*.png'):
                plot_files.append(str(plot_file))
                
            return True, "Polynomial plots generated successfully", {
                'plots': plot_files,
                'output': stdout
            }
            
        except Exception as e:
            return False, f"Error plotting polynomials: {str(e)}", None 