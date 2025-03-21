import subprocess
import os
from pathlib import Path
import shutil
from typing import Tuple, Optional, List, Dict
import json

class AWDService:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.submodule_dir = workspace_root / 'submodules/awd'
        
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

    def train_model(self, 
                   duck_type: str, 
                   num_envs: int,
                   motion_file: str,
                   task: str = "DucklingCommand") -> Tuple[bool, str, Optional[str]]:
        """Train a model using AWD."""
        try:
            cmd = [
                'python', 'awd/run.py',
                '--task', task,
                '--num_envs', str(num_envs),
                '--cfg_env', f'awd/data/cfg/{duck_type}/duckling_command.yaml',
                '--cfg_train', f'awd/data/cfg/{duck_type}/train/amp_duckling_task.yaml',
                '--motion_file', motion_file
            ]
            
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "Training failed", stderr
                
            return True, "Training started successfully", stdout
            
        except Exception as e:
            return False, f"Error starting training: {str(e)}", None

    def test_model(self,
                  duck_type: str,
                  num_envs: int,
                  motion_file: str,
                  checkpoint: str,
                  task: str = "DucklingCommand") -> Tuple[bool, str, Optional[str]]:
        """Test a trained model."""
        try:
            cmd = [
                'python', 'awd/run.py',
                '--test',
                '--task', task,
                '--num_envs', str(num_envs),
                '--cfg_env', f'awd/data/cfg/{duck_type}/duckling_command.yaml',
                '--cfg_train', f'awd/data/cfg/{duck_type}/train/amp_duckling_task.yaml',
                '--motion_file', motion_file,
                '--checkpoint', checkpoint
            ]
            
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "Testing failed", stderr
                
            return True, "Testing started successfully", stdout
            
        except Exception as e:
            return False, f"Error starting testing: {str(e)}", None

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