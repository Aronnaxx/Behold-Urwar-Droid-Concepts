import subprocess
import os
from pathlib import Path
import shutil
import logging
from typing import Tuple, Optional, List, Dict
from datetime import datetime
import traceback
from ..config import duck_config
from ..utils.command import run_command

class AWDService:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.submodule_dir = workspace_root / 'submodules/awd'
        self.logger = logging.getLogger(__name__)
        
    def train_model(self, duck_type: str, num_envs: int = 2048, motion_file: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """Train a model using Active Whole-Body Control for Humanoids (AWD)."""
        try:
            self.logger.info(f"Starting AWD training for {duck_type} with {num_envs} environments")
            
            # Validate duck type with duck_config
            duck_info = duck_config.get_config_by_internal_name(duck_type)
            if duck_info:
                self.logger.info(f"Found duck configuration for internal name {duck_type}")
                self.logger.debug(f"Duck Type: {duck_info['duck_type']}, Variant: {duck_info['variant']}")
            else:
                self.logger.warning(f"No duck configuration found for internal name {duck_type}")
                # Continue with the original duck_type

            # Prepare output directory
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.workspace_root / 'trained_models' / duck_type / f"awd_{run_id}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build command
            cmd = ['uv', 'run', '--active', 'awd/train.py']
            cmd.extend(['--duck_type', duck_type])
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
                self.logger.error("AWD training command failed")
                return False, "AWD training command failed", {
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
            latest_link = self.workspace_root / 'trained_models' / duck_type / 'latest_awd'
            if latest_link.exists():
                latest_link.unlink()
            latest_link.symlink_to(output_dir, target_is_directory=True)
            
            return True, "AWD training completed successfully", training_output
            
        except Exception as e:
            self.logger.error(f"Error in AWD training: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error in AWD training: {str(e)}", None
            
    def test_model(self, duck_type: str, model_path: str) -> Tuple[bool, str, Optional[Dict]]:
        """Test a trained AWD model."""
        try:
            self.logger.info(f"Testing AWD model for duck type {duck_type}: {model_path}")
            
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
            cmd = ['uv', 'run', '--active', 'awd/test.py']
            cmd.extend(['--duck_type', duck_type])
            cmd.extend(['--model', str(model_file)])
            
            # Run test command
            stdout, stderr, success = run_command(
                cmd, 
                str(self.submodule_dir),
                logger=self.logger
            )
            
            if not success:
                self.logger.error("AWD testing command failed")
                return False, "AWD testing command failed", {
                    'command': ' '.join(cmd),
                    'stdout': stdout,
                    'stderr': stderr
                }
                
            return True, "AWD testing completed successfully", {
                'command': ' '.join(cmd),
                'stdout': stdout,
                'stderr': stderr
            }
            
        except Exception as e:
            self.logger.error(f"Error testing AWD model: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error testing AWD model: {str(e)}", None
            
    def export_model(self, model_path: str, export_format: str = 'onnx') -> Tuple[bool, str, Optional[Dict]]:
        """Export a trained model to a specified format."""
        try:
            self.logger.info(f"Exporting model {model_path} to {export_format} format")
            
            # Check if model file exists
            model_file = Path(model_path)
            if not model_file.exists():
                return False, f"Model file not found: {model_path}", None
                
            # Create export directory
            export_dir = model_file.parent / 'exports'
            export_dir.mkdir(exist_ok=True)
            
            # Build command
            cmd = ['uv', 'run', '--active', 'awd/export.py']
            cmd.extend(['--model', str(model_file)])
            cmd.extend(['--format', export_format])
            cmd.extend(['--output_dir', str(export_dir)])
            
            # Run export command
            stdout, stderr, success = run_command(
                cmd, 
                str(self.submodule_dir),
                logger=self.logger
            )
            
            if not success:
                self.logger.error("Model export command failed")
                return False, "Model export command failed", {
                    'command': ' '.join(cmd),
                    'stdout': stdout,
                    'stderr': stderr
                }
                
            # Get list of exported files
            exported_files = list(export_dir.glob(f'*.{export_format}'))
            
            return True, f"Model exported successfully to {export_format}", {
                'command': ' '.join(cmd),
                'stdout': stdout,
                'stderr': stderr,
                'export_dir': str(export_dir),
                'exported_files': [str(f.name) for f in exported_files]
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting model: {str(e)}")
            self.logger.error(traceback.format_exc())
            return False, f"Error exporting model: {str(e)}", None

    def view_urdf(self, 
                 urdf_path: str,
                 frames: Optional[List[str]] = None) -> Tuple[bool, str, Optional[str]]:
        """View a URDF file."""
        try:
            cmd = ['python', 'view_urdf.py', urdf_path]
            
            if frames:
                cmd.extend(['--frames'] + frames)
                
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "URDF viewing failed", stderr
                
            return True, "URDF viewer launched successfully", stdout
            
        except Exception as e:
            return False, f"Error launching URDF viewer: {str(e)}", None

    def get_available_configs(self, duck_type: str) -> Dict[str, Dict]:
        """Get available configuration files for a duck type."""
        try:
            cfg_dir = self.submodule_dir / 'awd/data/cfg' / duck_type
            configs = {
                'env': {},
                'train': {}
            }
            
            if (cfg_dir / 'duckling_command.yaml').exists():
                configs['env']['command'] = 'duckling_command.yaml'
                
            train_dir = cfg_dir / 'train'
            if train_dir.exists():
                for cfg_file in train_dir.glob('*.yaml'):
                    configs['train'][cfg_file.stem] = str(cfg_file.relative_to(cfg_dir))
                    
            return configs
            
        except Exception:
            return {'env': {}, 'train': {}} 