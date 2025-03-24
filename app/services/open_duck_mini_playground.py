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
from ..config import duck_config
from ..utils.command import run_command

class OpenDuckPlaygroundService:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.submodule_dir = workspace_root / 'submodules/open_duck_playground'
        self.logger = logging.getLogger(__name__)
        
    def train_model(self, duck_type: str, num_envs: int = 2048, motion_file: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Train a model using the Open Duck Mini Playground."""
        try:
            self.logger.info(f"Starting training for {duck_type} with {num_envs} environments")
            
            # Validate duck type with duck_config
            duck_info = duck_config.get_config_by_internal_name(duck_type)
            if duck_info:
                self.logger.info(f"Found duck configuration for internal name {duck_type}")
                self.logger.debug(f"Duck Type: {duck_info['duck_type']}, Variant: {duck_info['variant']}")
            else:
                self.logger.warning(f"No duck configuration found for internal name {duck_type}")
                # Continue with the original duck_type

            # Prepare temp directory
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.workspace_root / 'trained_models' / duck_type / run_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = ['uv', 'run', '--active', 'train.py']
            cmd.extend(['--type', duck_type])
            cmd.extend(['--num_envs', str(num_envs)])
            
            if motion_file:
                motion_path = self.workspace_root / motion_file
                if not motion_path.exists():
                    return False, f"Motion file not found: {motion_file}", None
                cmd.extend(['--motion_file', str(motion_path)])
            
            # Add output directory
            cmd.extend(['--output_dir', str(output_dir)])
            
            # Log command
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            self.logger.debug(f"Working directory: {self.submodule_dir}")
            
            # Run training command
            stdout, stderr, success = run_command(
                cmd, 
                str(self.submodule_dir),
                logger=self.logger
            )
            
            if not success:
                self.logger.error("Training command failed")
                return False, "Training command failed", {
                    'command': ' '.join(cmd),
                    'stdout': stdout,
                    'stderr': stderr
                }
            
            # Prepare output
            training_output = {
                'command': ' '.join(cmd),
                'stdout': stdout,
                'stderr': stderr,
                'output_dir': str(output_dir),
                'model_files': []
            }
            
            # Get list of generated model files
            for model_file in output_dir.glob('*.pth'):
                training_output['model_files'].append(str(model_file.name))
            
            # Create latest symlink
            latest_link = self.workspace_root / 'trained_models' / duck_type / 'latest'
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(output_dir, target_is_directory=True)
            
            return True, "Training completed successfully", training_output
            
        except Exception as e:
            self.logger.error(f"Error training model: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error training model: {str(e)}", None
            
    def test_model(self, duck_type: str, model_path: str) -> Tuple[bool, str, Optional[Dict]]:
        """Test a trained model."""
        try:
            self.logger.info(f"Testing model for duck type {duck_type}: {model_path}")
            
            # Validate duck type with duck_config
            duck_info = duck_config.get_config_by_internal_name(duck_type)
            if duck_info:
                self.logger.info(f"Found duck configuration for internal name {duck_type}")
            else:
                self.logger.warning(f"No duck configuration found for internal name {duck_type}")
            
            # Check if model file exists
            model_file = Path(model_path)
            if not model_file.exists():
                return False, f"Model file not found: {model_path}", None
                
            # Build command
            cmd = ['uv', 'run', '--active', 'test.py']
            cmd.extend(['--type', duck_type])
            cmd.extend(['--model', str(model_file)])
            
            # Run test command
            stdout, stderr, success = run_command(
                cmd, 
                str(self.submodule_dir),
                logger=self.logger
            )
            
            if not success:
                self.logger.error("Testing command failed")
                return False, "Testing command failed", {
                    'command': ' '.join(cmd),
                    'stdout': stdout,
                    'stderr': stderr
                }
                
            return True, "Testing completed successfully", {
                'command': ' '.join(cmd),
                'stdout': stdout,
                'stderr': stderr
            }
            
        except Exception as e:
            self.logger.error(f"Error testing model: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error testing model: {str(e)}", None

    def check_process_running(self, process_name: str) -> bool:
        """Check if a process is running."""
        try:
            output = subprocess.check_output(['pgrep', '-f', process_name])
            return bool(output)
        except subprocess.CalledProcessError:
            return False

    def infer_model(self, duck_type: str, model_path: str = None, use_keyboard: bool = False) -> Tuple[bool, str, Optional[str]]:
        """Run inference using a trained model."""
        try:
            # If no model path provided, use the latest_best_walk.onnx
            if not model_path:
                model_path = str(self.workspace_root / f'trained_models/{duck_type}/latest_best_walk.onnx')
                self.logger.info(f"Using default model: {model_path}")
            
            # Ensure model file exists
            if not os.path.exists(model_path):
                return False, f"Model file not found: {model_path}", None
            
            # Use our urwar_run.py wrapper instead of direct uv commands
            script_path = f'submodules/open_duck_playground/playground/{duck_type}/mujoco_infer.py'
            
            cmd = [
                str(self.workspace_root / 'urwar_run.py'),
                script_path,
                '-o', model_path
            ]
            
            if use_keyboard:
                cmd.append('-k')
                
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            
            stdout, stderr, success = run_command(
                cmd, 
                str(self.workspace_root),
                logger=self.logger
            )
            
            if not success:
                self.logger.error("Inference command failed")
                return False, "Inference failed", stderr
                
            return True, "Inference started successfully", stdout
            
        except Exception as e:
            self.logger.error(f"Error starting inference: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error starting inference: {str(e)}", None

    def launch_playground(self, duck_type: str) -> Tuple[bool, str, Optional[str]]:
        """Launch the playground environment."""
        try:
            # Use our urwar_run.py wrapper
            script_path = f'submodules/open_duck_playground/playground/{duck_type}/runner.py'
            
            cmd = [
                str(self.workspace_root / 'urwar_run.py'),
                script_path
            ]
            
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            
            stdout, stderr, success = run_command(
                cmd, 
                str(self.workspace_root),
                logger=self.logger
            )
            
            if not success:
                self.logger.error("Playground launch failed")
                return False, "Playground launch failed", stderr
                
            return True, "Playground launched successfully", stdout
            
        except Exception as e:
            self.logger.error(f"Error launching playground: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error launching playground: {str(e)}", None

    def close_playground(self) -> Tuple[bool, str]:
        """Close the playground environment."""
        try:
            if self.playground_process:
                self.playground_process.terminate()
                self.playground_process = None
            return True, "Playground closed successfully"
        except Exception as e:
            return False, f"Error closing playground: {str(e)}" 