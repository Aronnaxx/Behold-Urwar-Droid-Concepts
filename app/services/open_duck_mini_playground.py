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
from ..config import duck_config, GENERATED_MOTIONS_DIR, TRAINED_MODELS_DIR
from ..utils.command import run_command

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class OpenDuckPlaygroundService:
    _instance = None
    _initialized = False

    def __new__(cls, workspace_root: Path):
        if cls._instance is None:
            cls._instance = super(OpenDuckPlaygroundService, cls).__new__(cls)
        return cls._instance

    def __init__(self, workspace_root: Path):
        if not self._initialized:
            self.workspace_root = workspace_root
            self.submodule_dir = workspace_root / 'submodules/open_duck_playground'
            self.logger = logging.getLogger(__name__)
            
            # Log initialization details
            self.logger.info("Initializing OpenDuckPlaygroundService")
            self.logger.debug(f"Workspace root: {workspace_root}")
            self.logger.debug(f"Submodule directory: {self.submodule_dir}")
            self.logger.debug(f"TRAINED_MODELS_DIR: {TRAINED_MODELS_DIR}")
            self.logger.debug(f"Current working directory: {os.getcwd()}")
            
            # Check if submodule directory exists
            if not self.submodule_dir.exists():
                self.logger.error(f"Submodule directory does not exist: {self.submodule_dir}")
                raise FileNotFoundError(f"Submodule directory not found: {self.submodule_dir}")
                
            # Check if submodule directory is a git repository
            try:
                subprocess.run(['git', 'rev-parse', '--git-dir'], 
                             cwd=self.submodule_dir, 
                             check=True, 
                             capture_output=True)
                self.logger.debug("Submodule directory is a valid git repository")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Submodule directory is not a git repository: {e}")
                self.logger.error(f"Git error output: {e.stderr.decode()}")
            
            # Available environments and tasks
            self.available_envs = {
                "joystick": {
                    "name": "Joystick Control",
                    "description": "Control the duck using a joystick interface",
                    "tasks": {
                        "flat_terrain": "Flat Ground",
                        "slope": "Sloped Surface",
                        "stairs": "Staircase",
                        "obstacles": "Obstacle Course"
                    }
                },
                "standing": {
                    "name": "Standing Balance",
                    "description": "Maintain balance while standing",
                    "tasks": {
                        "flat_terrain": "Flat Ground",
                        "slope": "Sloped Surface",
                        "disturbance": "External Disturbances"
                    }
                }
            }
            
            self.logger.debug(f"Available environments: {json.dumps(self.available_envs, indent=2)}")
            self._initialized = True
            
    def find_available_models(self, duck_type: str) -> List[Dict]:
        """Find all available models for a given duck type."""
        try:
            self.logger.info(f"Searching for available models for duck type: {duck_type}")
            
            # Get the base duck type and variant from the internal name
            duck_info = duck_config.find_by_internal_name(duck_type)
            if not duck_info:
                self.logger.warning(f"No duck info found for internal name: {duck_type}")
                return []
                
            base_duck_type = duck_info['duck_type']
            variant_id = duck_info['variant']  # This will be 'v1', 'v2', etc.
            self.logger.debug(f"Base duck type: {base_duck_type}, Variant: {variant_id}")
            
            # Base directory for the duck type - using variant ID instead of internal name
            base_dir = self.workspace_root / TRAINED_MODELS_DIR / base_duck_type / variant_id
            self.logger.debug(f"Searching in base directory: {base_dir}")
            
            if not base_dir.exists():
                self.logger.warning(f"Base directory does not exist: {base_dir}")
                return []
            
            available_models = []
            
            # First, look for any .onnx files directly in the variant directory
            direct_onnx_files = list(base_dir.glob('*.onnx'))
            for onnx_file in direct_onnx_files:
                self.logger.debug(f"Found standalone .onnx file: {onnx_file}")
                model_info = {
                    'path': str(onnx_file.parent),
                    'variant': variant_id,
                    'files': [onnx_file.name],
                    'is_latest': False,
                    'timestamp': datetime.fromtimestamp(onnx_file.stat().st_mtime).strftime('%Y%m%d_%H%M%S'),
                    'type': 'standalone'
                }
                available_models.append(model_info)
            
            # Then look for model directories
            model_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
            self.logger.debug(f"Found model directories: {[d.name for d in model_dirs]}")
            
            for model_dir in model_dirs:
                # Look for .onnx files in each directory
                onnx_files = list(model_dir.glob('*.onnx'))
                if onnx_files:
                    self.logger.debug(f"Found {len(onnx_files)} .onnx files in {model_dir}")
                    is_latest = model_dir.name.startswith('latest_')
                    
                    model_info = {
                        'path': str(model_dir),
                        'variant': variant_id,
                        'files': [f.name for f in onnx_files],
                        'is_latest': is_latest,
                        'timestamp': model_dir.name.split('_')[0] if not is_latest else datetime.fromtimestamp(model_dir.stat().st_mtime).strftime('%Y%m%d_%H%M%S'),
                        'type': 'latest' if is_latest else 'timestamped'
                    }
                    available_models.append(model_info)
                    self.logger.debug(f"Added model info: {model_info}")
            
            # Sort by timestamp if available, putting latest models first
            available_models.sort(key=lambda x: (not x['is_latest'], x['timestamp'] if x['timestamp'] else ''), reverse=True)
            
            self.logger.info(f"Found {len(available_models)} available models")
            for model in available_models:
                self.logger.debug(f"Model: {model['type']} - {model['path']} ({len(model['files'])} files)")
            
            return available_models
            
        except Exception as e:
            self.logger.error(f"Error finding available models: {str(e)}")
            self.logger.error(traceback.format_exc())
            return []
            
    def get_latest_model_path(self, duck_type: str) -> Optional[str]:
        """Get the path to the latest model for a given duck type."""
        try:
            self.logger.info(f"Getting latest model path for duck type: {duck_type}")
            
            # Get the base duck type and variant from the internal name
            duck_info = duck_config.find_by_internal_name(duck_type)
            if not duck_info:
                self.logger.error(f"No duck info found for internal name: {duck_type}")
                return None
                
            base_duck_type = duck_info['duck_type']
            variant_id = duck_info['variant']  # This will be 'v1', 'v2', etc.
            self.logger.debug(f"Base duck type: {base_duck_type}, Variant: {variant_id}")
            
            # Base directory for the duck type - using variant ID instead of internal name
            base_dir = self.workspace_root / TRAINED_MODELS_DIR / base_duck_type / variant_id
            self.logger.debug(f"Checking base directory: {base_dir}")
            
            if not base_dir.exists():
                self.logger.error(f"Base directory does not exist: {base_dir}")
                return None
            
            # Look for latest model directory
            latest_dirs = [d for d in base_dir.iterdir() if d.is_dir() and d.name.startswith('latest_')]
            if not latest_dirs:
                self.logger.error(f"No latest model found for {duck_type}")
                return None
                
            # Use the most recently modified latest directory
            latest_dir = max(latest_dirs, key=lambda d: d.stat().st_mtime)
            self.logger.debug(f"Found latest model directory: {latest_dir}")
            
            # Look for .onnx file
            onnx_files = list(latest_dir.glob('*.onnx'))
            if not onnx_files:
                self.logger.error(f"No .onnx file found in {latest_dir}")
                return None
                
            # Use the first .onnx file found
            model_path = str(onnx_files[0])
            self.logger.info(f"Using latest model: {model_path}")
            return model_path
            
        except Exception as e:
            self.logger.error(f"Error getting latest model path: {str(e)}")
            self.logger.error(traceback.format_exc())
            return None
        
    def train_model(self, 
                   duck_type: str, 
                   variant: str = None,
                   **params) -> Tuple[bool, str, Optional[Dict]]:
        """Train a model using the runner.py script."""
        try:
            self.logger.info(f"Starting model training for {duck_type} (variant: {variant})")
            self.logger.debug(f"Parameters received: {params}")
            
            # Add more detailed parameter logging
            self.logger.info("----- Model Training Parameters -----")
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
            
            # Create output directory using TRAINED_MODELS_DIR
            output_dir = self.workspace_root / TRAINED_MODELS_DIR / duck_type
            self.logger.debug(f"Creating output directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Created output directory: {output_dir}")
            
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            self.logger.debug(f"Created run ID: {run_id}")
            
            with tempfile.TemporaryDirectory(prefix=f'training_{run_id}_') as temp_dir:
                temp_dir_path = Path(temp_dir)
                self.logger.debug(f"Created temporary directory: {temp_dir_path}")
                
                # Create subdirectories
                log_dir = temp_dir_path / 'log'
                tmp_dir = temp_dir_path / 'tmp'
                self.logger.debug(f"Creating log directory: {log_dir}")
                self.logger.debug(f"Creating tmp directory: {tmp_dir}")
                log_dir.mkdir(exist_ok=True)
                tmp_dir.mkdir(exist_ok=True)
                
                # Build command
                cmd = ['uv', 'run', '--active', f'playground/{duck_type}/runner.py']
                self.logger.debug(f"Base command: {cmd}")
                
                # Add required parameters
                cmd.extend(['--output_dir', str(temp_dir_path)])
                cmd.extend(['--num_timesteps', str(params.get('num_timesteps', '150000000'))])
                
                # Validate and add environment and task
                env = params.get('env', 'joystick')
                task = params.get('task', 'flat_terrain')
                
                self.logger.debug(f"Validating environment: {env}")
                self.logger.debug(f"Validating task: {task}")
                
                if env not in self.available_envs:
                    self.logger.error(f"Invalid environment: {env}")
                    return False, f"Invalid environment: {env}. Available: {list(self.available_envs.keys())}", None
                    
                if task not in self.available_envs[env]['tasks']:
                    self.logger.error(f"Invalid task: {task} for environment {env}")
                    return False, f"Invalid task: {task} for environment {env}. Available: {list(self.available_envs[env]['tasks'].keys())}", None
                
                cmd.extend(['--env', env])
                cmd.extend(['--task', task])
                
                if params.get('restore_checkpoint_path'):
                    self.logger.debug(f"Adding restore checkpoint path: {params['restore_checkpoint_path']}")
                    cmd.extend(['--restore_checkpoint_path', params['restore_checkpoint_path']])
                
                # More detailed command logging
                self.logger.info(f"Executing command: {' '.join(cmd)}")
                self.logger.debug(f"Command as list: {cmd}")
                self.logger.debug(f"Working directory: {self.submodule_dir}")
                self.logger.debug(f"Duck type: {duck_type}")
                self.logger.debug(f"Temp directory: {temp_dir_path}")
                
                # Check if runner.py exists
                runner_path = self.submodule_dir / 'playground' / duck_type / 'runner.py'
                self.logger.debug(f"Checking if runner.py exists at: {runner_path}")
                if not runner_path.exists():
                    self.logger.error(f"runner.py not found at: {runner_path}")
                    return False, f"runner.py not found at: {runner_path}", None
                
                # Run training command using the utility function
                self.logger.debug("Starting command execution...")
                stdout, stderr, success = run_command(cmd, str(self.submodule_dir), logger=self.logger)
                
                if not success:
                    self.logger.error("Training command failed")
                    self.logger.error(f"Command output: {stdout}")
                    self.logger.error(f"Error output: {stderr}")
                    return False, "Training command failed", {
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
                
                # Wait for model files
                self.logger.info("Waiting for model files to be generated...")
                max_wait = 30
                wait_interval = 0.5
                waited = 0
                
                while waited < max_wait:
                    model_files = list(temp_dir_path.glob('*.onnx'))
                    if model_files:
                        self.logger.info(f"Found {len(model_files)} model files after {waited}s")
                        self.logger.debug(f"Model files found: {[f.name for f in model_files]}")
                        break
                    self.logger.debug(f"No model files found yet, waiting {wait_interval}s...")
                    time.sleep(wait_interval)
                    waited += wait_interval
                
                if not model_files:
                    self.logger.error("No model files were generated")
                    self.logger.error(f"Directory contents: {list(temp_dir_path.iterdir())}")
                    return False, "No model files were generated after waiting 30s", {
                        'output': '\n'.join(log_output)
                    }
                
                # Create run-specific output directory and copy files
                try:
                    self.logger.info("Copying generated files to output directory...")
                    run_output_dir = output_dir / run_id
                    self.logger.debug(f"Creating run output directory: {run_output_dir}")
                    run_output_dir.mkdir(exist_ok=True)
                    
                    for file in model_files:
                        dest_file = run_output_dir / file.name
                        self.logger.debug(f"Copying {file} to {dest_file}")
                        shutil.copy2(file, dest_file)
                    
                    # Update latest symlink
                    latest_link = output_dir / f'latest_{duck_type}'
                    self.logger.debug(f"Updating symlink {latest_link} -> {run_output_dir}")
                    if latest_link.exists():
                        self.logger.debug("Removing existing symlink")
                        latest_link.unlink()
                    latest_link.symlink_to(run_output_dir, target_is_directory=True)
                    
                except Exception as e:
                    self.logger.error(f"Error copying generated files: {str(e)}")
                    self.logger.error(traceback.format_exc())
                    return False, f"Error copying generated files: {str(e)}", {
                        'output': '\n'.join(log_output)
                    }
                
                self.logger.info("Model training completed successfully")
                return True, "Model training completed successfully", {
                    'output': '\n'.join(log_output),
                    'files': [str(f.name) for f in model_files],
                    'run_id': run_id,
                    'env': env,
                    'task': task
                }
                
        except Exception as e:
            self.logger.error(f"Unexpected error in model training: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Model training failed: {str(e)}", {
                'error': str(e),
                'traceback': traceback.format_exc()
            }
            
    def run_inference(self,
                     duck_type: str,
                     variant: str = None,
                     **params) -> Tuple[bool, str, Optional[Dict]]:
        """Run inference using mujoco_infer.py."""
        try:
            self.logger.info(f"Starting inference for {duck_type} (variant: {variant})")
            self.logger.debug(f"Parameters received: {params}")
            
            # Add more detailed parameter logging
            self.logger.info("----- Inference Parameters -----")
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
            cmd = ['uv', 'run', '--active', f'playground/{duck_type}/mujoco_infer.py']
            
            # Add required parameters
            if not params.get('onnx_model_path'):
                self.logger.error("ONNX model path is required")
                return False, "ONNX model path is required", None
                
            cmd.extend(['-o', params['onnx_model_path']])
            self.logger.debug(f"Using ONNX model path: {params['onnx_model_path']}")
            
            # Add optional parameters
            if params.get('reference_data'):
                cmd.extend(['--reference_data', params['reference_data']])
            if params.get('model_path'):
                cmd.extend(['--model_path', params['model_path']])
            if params.get('standing'):
                cmd.append('--standing')
                
            # Add environment and task if specified
            env = params.get('env')
            task = params.get('task')
            if env and task:
                if env not in self.available_envs:
                    self.logger.error(f"Invalid environment: {env}")
                    return False, f"Invalid environment: {env}. Available: {list(self.available_envs.keys())}", None
                if task not in self.available_envs[env]['tasks']:
                    self.logger.error(f"Invalid task: {task} for environment {env}")
                    return False, f"Invalid task: {task} for environment {env}. Available: {list(self.available_envs[env]['tasks'].keys())}", None
                cmd.extend(['--env', env])
                cmd.extend(['--task', task])
            
            # More detailed command logging
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            self.logger.debug(f"Command as list: {cmd}")
            self.logger.debug(f"Working directory: {self.submodule_dir}")
            self.logger.debug(f"Duck type: {duck_type}")
            
            # Run inference command using the utility function
            stdout, stderr, success = run_command(cmd, str(self.submodule_dir), logger=self.logger)
            
            if not success:
                self.logger.error("Inference command failed")
                return False, "Inference command failed", {
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
            
            self.logger.info("Inference completed successfully")
            return True, "Inference completed successfully", {
                'output': '\n'.join(log_output),
                'env': env,
                'task': task
            }
            
        except Exception as e:
            self.logger.error(f"Unexpected error in inference: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Inference failed: {str(e)}", {
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    def launch_playground(self, 
                         duck_type: str,
                         model: str = 'latest',
                         env: str = 'joystick',
                         task: str = 'flat_terrain',
                         speed: int = 50) -> Tuple[bool, str, Optional[Dict]]:
        """Launch the playground with the specified parameters."""
        try:
            self.logger.info(f"Launching playground for {duck_type}")
            self.logger.debug(f"Parameters: model={model}, env={env}, task={task}, speed={speed}")
            
            # Get model path
            if model == 'latest':
                model_path = self.get_latest_model_path(duck_type)
                if not model_path:
                    self.logger.error(f"No latest model found for {duck_type}")
                    return False, f"No latest model found for {duck_type}", None
            else:
                # Handle other model selection methods
                self.logger.error(f"Unsupported model selection: {model}")
                return False, f"Unsupported model selection: {model}", None
            
            self.logger.debug(f"Using model path: {model_path}")
            
            # Build command - only pass the required ONNX model path
            cmd = ['uv', 'run', '--active', f'playground/{duck_type}/mujoco_infer.py']
            cmd.extend(['-o', model_path])
            
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            self.logger.debug(f"Working directory: {self.submodule_dir}")
            
            # Get current environment and ensure DISPLAY is set
            current_env = os.environ.copy()
            if 'DISPLAY' not in current_env:
                current_env['DISPLAY'] = ':0'  # Default to primary display
            
            # Run command using Popen without capturing output
            process = subprocess.Popen(
                cmd,
                cwd=str(self.submodule_dir),
                env=current_env,
                stdout=None,  # Don't capture stdout
                stderr=None,  # Don't capture stderr
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0  # Windows-specific flag
            )
            
            # Store process for later management if needed
            self._current_playground_process = process
            
            self.logger.info("Playground launched successfully")
            return True, "Playground launched successfully", {
                'model_path': model_path,
                'process_id': process.pid
            }
            
        except Exception as e:
            self.logger.error(f"Error launching playground: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error launching playground: {str(e)}", {
                'error': str(e),
                'traceback': traceback.format_exc()
            }