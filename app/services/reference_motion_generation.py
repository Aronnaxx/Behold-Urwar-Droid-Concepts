import subprocess
import os
from pathlib import Path
import shutil
import time
import json
import logging
from typing import Tuple, Optional, List, Dict
import tempfile
from datetime import datetime
import traceback
from ..config import duck_config, GENERATED_MOTIONS_DIR
from ..utils.command import run_command

class ReferenceMotionGenerationService:
    _instance = None
    _initialized = False

    def __new__(cls, workspace_root: Path):
        if cls._instance is None:
            cls._instance = super(ReferenceMotionGenerationService, cls).__new__(cls)
        return cls._instance

    def __init__(self, workspace_root: Path):
        if not self._initialized:
            self.workspace_root = workspace_root
            self.submodule_dir = workspace_root / 'submodules/open_duck_reference_motion_generator'
            self.logger = logging.getLogger(__name__)
            self._initialized = True
        
    def generate_motion(self, 
                       duck_type: str, 
                       variant: str = None,
                       mode: str = 'auto',
                       **params) -> Tuple[bool, str, Optional[Dict]]:
        """Generate reference motions for the duck."""
        try:
            self.logger.info(f"Starting motion generation for {duck_type} (variant: {variant}) in {mode} mode")
            self.logger.debug(f"Parameters received: {params}")
            
            # Add more detailed parameter logging
            self.logger.info("----- Motion Generation Parameters -----")
            self.logger.info(f"Duck Type: {duck_type}")
            self.logger.info(f"Variant: {variant}")
            self.logger.info(f"Mode: {mode}")
            
            # Log all parameters with their types
            for key, value in params.items():
                self.logger.info(f"Parameter: {key} = {value} (type: {type(value).__name__})")
            
            self.logger.info("---------------------------------------")
            
            # Get duck information using the internal name
            duck_info = duck_config.find_by_internal_name(duck_type)
            if not duck_info:
                self.logger.error(f"No duck info found for internal name: {duck_type}")
                return False, f"No duck info found for internal name: {duck_type}", None
                
            base_duck_type = duck_info['duck_type']
            variant_id = duck_info['variant']  # This will be 'v1', 'v2', etc.
            self.logger.debug(f"Base duck type: {base_duck_type}, Variant: {variant_id}")
            
            # Base directory for the duck type - using variant ID instead of internal name
            output_dir = self.workspace_root / GENERATED_MOTIONS_DIR / base_duck_type / variant_id
            self.logger.debug(f"Using output directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            self.logger.debug(f"Created run ID: {run_id}")
            
            with tempfile.TemporaryDirectory(prefix=f'motion_gen_{run_id}_') as temp_dir:
                temp_dir_path = Path(temp_dir)
                (temp_dir_path / 'log').mkdir(exist_ok=True)
                (temp_dir_path / 'tmp').mkdir(exist_ok=True)
                
                self.logger.debug(f"Created temporary directory: {temp_dir_path}")
                
                # Build command
                if mode == 'auto':
                    generation_type = params.get('generation_type')
                    self.logger.debug(f"Auto mode with generation type: {generation_type}")
                    
                    cmd = ['uv', 'run', '--active', 'scripts/auto_waddle.py']
                    
                    # Use the internal duck_type name which is expected by the script
                    cmd.extend(['--duck', duck_type])
                    self.logger.info(f"Using duck type '{duck_type}' for auto_waddle.py script")
                    
                    if generation_type == 'sweep':
                        self.logger.debug("Using sweep generation")
                        cmd.append('--sweep')
                    elif generation_type == 'random':
                        num_motions = params.get('num_motions', '10')
                        self.logger.debug(f"Using random generation with {num_motions} motions")
                        cmd.extend(['--num', num_motions])
                    else:  # single motion
                        self.logger.debug("Using single motion generation")
                        cmd.extend(['--num', '1'])
                else:
                    self.logger.debug("Using advanced mode with gait generator")
                    cmd = ['uv', 'run', '--active', 'open_duck_reference_motion_generator/gait_generator.py']
                    
                    # Also use the internal duck_type name for gait_generator.py
                    cmd.extend(['--duck', duck_type])
                    cmd.extend(['--name', f'motion_{run_id}'])
                    
                    # Process all advanced parameters
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
                    
                    self.logger.debug(f"Advanced parameters: {advanced_params}")
                    for param_name, value in advanced_params.items():
                        if value is not None:
                            cmd.extend([f'--{param_name}', str(value)])
                
                cmd.extend(['--output_dir', str(temp_dir_path)])
                
                # More detailed command logging
                self.logger.info(f"Executing command: {' '.join(cmd)}")
                self.logger.debug(f"Command as list: {cmd}")
                self.logger.debug(f"Working directory: {self.submodule_dir}")
                self.logger.debug(f"Duck type: {duck_type}")
                self.logger.debug(f"Temp directory: {temp_dir_path}")
                
                # Run motion generation command using the utility function
                stdout, stderr, success = run_command(cmd, str(self.submodule_dir), logger=self.logger)
                
                if not success:
                    self.logger.error("Motion generation command failed")
                    return False, "Motion generation command failed", {
                        'command': ' '.join(cmd),
                        'stdout': stdout,
                        'stderr': stderr
                    }
                
                self.logger.debug("Command executed successfully")
                
                log_output = []
                if stdout:
                    log_output.append("Command Output:")
                    log_output.extend(stdout.split('\n'))
                    self.logger.debug(f"Command output: {stdout}")
                
                if stderr:
                    if "Failed to uninstall package" in stderr or "Installed" in stderr:
                        log_output.append("\nPackage Installation Messages:")
                        log_output.extend(stderr.split('\n'))
                        self.logger.debug(f"Package messages: {stderr}")
                    else:
                        log_output.append("\nErrors:")
                        log_output.extend(stderr.split('\n'))
                        self.logger.warning(f"Command errors: {stderr}")
                
                # Wait for motion files
                self.logger.info("Waiting for motion files to be generated...")
                max_wait = 30
                wait_interval = 0.5
                waited = 0
                
                while waited < max_wait:
                    motion_files = list(temp_dir_path.glob('*.json'))
                    if motion_files:
                        self.logger.info(f"Found {len(motion_files)} motion files after {waited}s")
                        break
                    time.sleep(wait_interval)
                    waited += wait_interval
                
                if not motion_files:
                    self.logger.error("No motion files were generated")
                    return False, "No motion files were generated after waiting 30s", {
                        'output': '\n'.join(log_output)
                    }
                
                # List the found motion files for debugging
                self.logger.debug(f"Motion files found: {[f.name for f in motion_files]}")
                
                # Fit polynomials
                self.logger.info("Fitting polynomials to motion data...")
                # fit_cmd = ['uv', 'run', '--active', 'scripts/fit_poly.py', '--ref_motion'] + [str(f) for f in motion_files]


                # Get highest numbered motion file
                # TODO: ask if this is correct 
                highest_num = max(int(f.name.split('_')[0]) for f in motion_files)
                fit_cmd = ['uv', 'run', '--active', 'scripts/fit_poly.py', '--ref_motion'] + [str(f) for f in motion_files if f.name.startswith(f'{highest_num}_')]

                self.logger.debug(f"Executing fit command: {' '.join(fit_cmd)}")
                
                fit_stdout, fit_stderr, fit_success = run_command(fit_cmd, str(self.submodule_dir), logger=self.logger)
                
                if not fit_success:
                    self.logger.error("Polynomial fitting failed")
                    return False, "Polynomial fitting failed", {
                        'command': ' '.join(fit_cmd),
                        'stdout': fit_stdout,
                        'stderr': fit_stderr,
                        'previous_output': '\n'.join(log_output)
                    }
                
                self.logger.debug("Polynomial fitting succeeded")
                
                if fit_stdout:
                    log_output.append("\nPolynomial Fitting Output:")
                    log_output.extend(fit_stdout.split('\n'))
                    self.logger.debug(f"Fit output: {fit_stdout}")
                if fit_stderr and not ("Uninstalled" in fit_stderr or "Installed" in fit_stderr):
                    log_output.append("\nPolynomial Fitting Errors:")
                    log_output.extend(fit_stderr.split('\n'))
                    self.logger.warning(f"Fit errors: {fit_stderr}")
                
                # Wait for polynomial coefficients file
                self.logger.info("Waiting for polynomial coefficients file...")
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
                        self.logger.info(f"Found polynomial coefficients file at {pkl_file} after {waited}s")
                        break
                    time.sleep(wait_interval)
                    waited += wait_interval
                
                if not pkl_file:
                    self.logger.error("No polynomial coefficients file was generated")
                    # Check the directory contents
                    self.logger.debug(f"Temp directory contents: {list(temp_dir_path.glob('*'))}")
                    self.logger.debug(f"Submodule directory contents: {list(self.submodule_dir.glob('*.pkl'))}")
                    return False, "No polynomial coefficients file was generated after waiting 30s", {
                        'output': '\n'.join(log_output)
                    }
                
                # Create run-specific output directory and copy files
                try:
                    self.logger.info("Copying generated files to output directory...")
                    run_output_dir = output_dir / run_id
                    run_output_dir.mkdir(exist_ok=True)
                    
                    for file in motion_files:
                        dest_file = run_output_dir / file.name
                        self.logger.debug(f"Copying {file} to {dest_file}")
                        shutil.copy2(file, dest_file)
                    
                    dest_pkl = run_output_dir / pkl_file.name
                    self.logger.debug(f"Copying {pkl_file} to {dest_pkl}")
                    shutil.copy2(pkl_file, dest_pkl)
                    
                    # Update latest symlink - using variant-specific path
                    latest_link = output_dir / f'latest_{variant_id}'
                    self.logger.debug(f"Updating symlink {latest_link} -> {run_output_dir}")
                    if latest_link.exists():
                        latest_link.unlink()
                    latest_link.symlink_to(run_output_dir, target_is_directory=True)
                    
                    # Copy to playground if needed
                    try:
                        playground_pkl_path = self.workspace_root / 'submodules/open_duck_playground/playground' / base_duck_type / 'data' / pkl_file.name
                        playground_pkl_path.parent.mkdir(parents=True, exist_ok=True)
                        self.logger.debug(f"Copying {pkl_file} to playground: {playground_pkl_path}")
                        shutil.copy2(pkl_file, playground_pkl_path)
                    except Exception as e:
                        self.logger.warning(f"Error copying files to playground: {str(e)}")
                        log_output.append(f"\nWarning: Error copying files to playground: {str(e)}")
                    
                except Exception as e:
                    self.logger.error(f"Error copying generated files: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    return False, f"Error copying generated files: {str(e)}", {
                        'output': '\n'.join(log_output)
                    }
                
                # Prepare motion data for frontend visualization
                try:
                    sample_motion_file = motion_files[0]
                    self.logger.debug(f"Reading sample motion file for preview: {sample_motion_file}")
                    with open(sample_motion_file, 'r') as f:
                        motion_data = json.load(f)
                        
                    self.logger.info("Motion generation completed successfully")
                    return True, "Motion generation completed successfully", {
                        'output': '\n'.join(log_output),
                        'files': [str(f.name) for f in motion_files],
                        'run_id': run_id,
                        'frames': motion_data.get('frames', [])  # Add frames for frontend visualization
                    }
                except Exception as e:
                    self.logger.warning(f"Error reading motion data for preview: {str(e)}")
                    # Continue with success even if preview data extraction fails
                    return True, "Motion generation completed successfully (preview unavailable)", {
                        'output': '\n'.join(log_output),
                        'files': [str(f.name) for f in motion_files],
                        'run_id': run_id
                    }
                
        except Exception as e:
            self.logger.error(f"Unexpected error in motion generation: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Motion generation failed: {str(e)}", {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
    def gait_playground(self, 
                       duck_type: str, 
                       variant: str = None,
                       **params) -> Tuple[bool, str, Optional[Dict]]:
        """Gait playground for reference motions for the duck."""
        try:
            self.logger.info(f"Starting gait playground for {duck_type} (variant: {variant})")
            self.logger.debug(f"Parameters received: {params}")
            
            # Add more detailed parameter logging
            self.logger.info("----- Gait Playground Parameters -----")
            self.logger.info(f"Duck Type: {duck_type}")
            self.logger.info(f"Variant: {variant}")
            
            # Log all parameters with their types
            for key, value in params.items():
                self.logger.info(f"Parameter: {key} = {value} (type: {type(value).__name__})")
            
            self.logger.info("---------------------------------------")
            
            # Get duck information using the internal name
            duck_info = duck_config.get_config_by_internal_name(duck_type)
            if duck_info:
                self.logger.info(f"Found duck configuration for internal name {duck_type}")
                self.logger.debug(f"Duck Type: {duck_info['duck_type']}, Variant: {duck_info['variant']}")
            else:
                self.logger.warning(f"No duck configuration found for internal name {duck_type}")

            # Build command
            cmd = ['uv', 'run', '--active', 'open_duck_reference_motion_generator/gait_playground.py']
                    
            # Use the internal duck_type name which is expected by the script
            cmd.extend(['--duck', duck_type])
            self.logger.info(f"Using duck type '{duck_type}' for gait_playground.py script")
            
            # Add any additional parameters
            for key, value in params.items():
                if value is not None:
                    cmd.extend([f'--{key}', str(value)])
            
            # Run the command
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            self.logger.debug(f"Command as list: {cmd}")
            self.logger.debug(f"Working directory: {self.submodule_dir}")
            
            stdout, stderr, success = run_command(cmd, str(self.submodule_dir), logger=self.logger)
            
            if not success:
                self.logger.error("Gait playground command failed")
                return False, "Gait playground command failed", {
                    'command': ' '.join(cmd),
                    'stdout': stdout,
                    'stderr': stderr
                }
            
            self.logger.info("Gait playground launched successfully")
            return True, "Gait playground launched successfully", {
                'stdout': stdout,
                'stderr': stderr
            }

        except Exception as e:
            self.logger.error(f"Unexpected error in gait playground: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Gait playground failed: {str(e)}", {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
        
    def list_motion_files(self, duck_type: str, variant: str = None) -> List[str]:
        """List available motion files for a specific duck type."""
        try:
            self.logger.debug(f"Listing motion files for {duck_type} (variant: {variant})")
            
            # Get the base duck type and variant from the internal name
            duck_info = duck_config.find_by_internal_name(duck_type)
            if not duck_info:
                self.logger.warning(f"No duck info found for internal name: {duck_type}")
                return []
                
            base_duck_type = duck_info['duck_type']
            variant_id = duck_info['variant']  # This will be 'v1', 'v2', etc.
            self.logger.debug(f"Base duck type: {base_duck_type}, Variant: {variant_id}")
            
            # Check motion directory using variant ID
            motion_dir = self.workspace_root / GENERATED_MOTIONS_DIR / base_duck_type / variant_id
            if not motion_dir.exists():
                self.logger.debug(f"Motion directory does not exist: {motion_dir}")
                return []
            
            # Get a list of available motion files
            motion_files = []
            for run_dir in motion_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                    
                self.logger.debug(f"Checking run directory: {run_dir}")
                for file in run_dir.glob('*.json'):
                    motion_files.append({
                        'name': file.name,
                        'path': str(file.relative_to(self.workspace_root)),
                        'date': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    })
            
            # Sort by date (newest first)
            motion_files.sort(key=lambda x: x['date'], reverse=True)
            self.logger.debug(f"Found {len(motion_files)} motion files")
            
            return motion_files
            
        except Exception as e:
            self.logger.error(f"Error listing motion files: {str(e)}")
            self.logger.error(traceback.format_exc())
            return []

    def list_training_files(self, duck_type):
        """
        List all training files available for a specific duck type.
        """
        self.logger.debug(f"Listing training files for {duck_type}")
        
        try:
            # If we're passed an internal name, resolve it to the duck type
            duck_info = duck_config.find_by_internal_name(duck_type)
            if duck_info:
                duck_type = duck_info['duck_type']
                self.logger.debug(f"Resolved internal name {duck_type} to duck type {duck_info['duck_type']}")
            
            # Construct path to training directory
            training_dir = self.workspace_root / 'training' / duck_type
            self.logger.debug(f"Looking for training files in directory: {training_dir}")
            
            # Check if directory exists
            if not training_dir.exists():
                self.logger.debug(f"Training directory does not exist: {training_dir}")
                return []
            
            # List all relevant training files
            training_files = []
            for root, dirs, files in os.walk(training_dir):
                for filename in files:
                    # Check for common training file extensions
                    if filename.endswith(('.pth', '.pt', '.h5', '.model', '.weights')):
                        filepath = os.path.join(root, filename)
                        file_info = {
                            'name': filename,
                            'path': filepath,
                            'size': os.path.getsize(filepath),
                            'created': os.path.getctime(filepath),
                            'modified': os.path.getmtime(filepath)
                        }
                        training_files.append(file_info)
            
            self.logger.debug(f"Found {len(training_files)} training files for {duck_type}")
            return training_files
            
        except Exception as e:
            self.logger.error(f"Error listing training files for {duck_type}: {str(e)}")
            return []
    
    def list_testing_files(self, duck_type):
        """
        List all testing files available for a specific duck type.
        """
        self.logger.debug(f"Listing testing files for {duck_type}")
        
        try:
            # If we're passed an internal name, resolve it to the duck type
            duck_info = duck_config.find_by_internal_name(duck_type)
            if duck_info:
                duck_type = duck_info['duck_type']
                self.logger.debug(f"Resolved internal name {duck_type} to duck type {duck_info['duck_type']}")
            
            # Construct path to testing directory
            testing_dir = self.workspace_root / 'testing' / duck_type
            self.logger.debug(f"Looking for testing files in directory: {testing_dir}")
            
            # Check if directory exists
            if not testing_dir.exists():
                self.logger.debug(f"Testing directory does not exist: {testing_dir}")
                return []
            
            # List all relevant testing files
            testing_files = []
            for root, dirs, files in os.walk(testing_dir):
                for filename in files:
                    # Check for common testing/validation file extensions
                    if filename.endswith(('.json', '.csv', '.txt', '.log')):
                        filepath = os.path.join(root, filename)
                        file_info = {
                            'name': filename,
                            'path': filepath,
                            'size': os.path.getsize(filepath),
                            'created': os.path.getctime(filepath),
                            'modified': os.path.getmtime(filepath)
                        }
                        testing_files.append(file_info)
            
            self.logger.debug(f"Found {len(testing_files)} testing files for {duck_type}")
            return testing_files
            
        except Exception as e:
            self.logger.error(f"Error listing testing files for {duck_type}: {str(e)}")
            return [] 