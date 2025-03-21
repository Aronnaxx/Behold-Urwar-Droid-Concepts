import subprocess
import os
from pathlib import Path
import shutil
from typing import Tuple, Optional, List

class OpenDuckPlaygroundService:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.playground_process = None
        self.submodule_dir = workspace_root / 'submodules/open_duck_playground'

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

    def check_process_running(self, process_name: str) -> bool:
        """Check if a process is running."""
        try:
            output = subprocess.check_output(['pgrep', '-f', process_name])
            return bool(output)
        except subprocess.CalledProcessError:
            return False

    def train_model(self, duck_type: str, num_envs: int, motion_file: str) -> Tuple[bool, str, Optional[str]]:
        """Train a model using the open duck playground."""
        try:
            cmd = [
                'uv', 'run', 'playground/runner.py',
                '--task', 'DucklingCommand',
                '--num_envs', str(num_envs),
                '--cfg_env', f'playground/{duck_type}/duckling_command.yaml',
                '--cfg_train', f'playground/{duck_type}/train/amp_duckling_task.yaml',
                '--motion_file', motion_file
            ]
            
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "Training failed", stderr
                
            return True, "Training started successfully", stdout
            
        except Exception as e:
            return False, f"Error starting training: {str(e)}", None

    def infer_model(self, duck_type: str, model_path: str, use_keyboard: bool = False) -> Tuple[bool, str, Optional[str]]:
        """Run inference using a trained model."""
        try:
            cmd = [
                'uv', 'run', f'playground/{duck_type}/mujoco_infer.py',
                '-o', model_path
            ]
            
            if use_keyboard:
                cmd.append('-k')
                
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "Inference failed", stderr
                
            return True, "Inference started successfully", stdout
            
        except Exception as e:
            return False, f"Error starting inference: {str(e)}", None

    def launch_playground(self, duck_type: str) -> Tuple[bool, str, Optional[str]]:
        """Launch the playground environment."""
        try:
            cmd = ['uv', 'run', f'playground/{duck_type}/runner.py']
            stdout, stderr = self.run_command(cmd, str(self.submodule_dir))
            
            if stderr and not ("Uninstalled" in stderr or "Installed" in stderr):
                return False, "Playground launch failed", stderr
                
            return True, "Playground launched successfully", stdout
            
        except Exception as e:
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