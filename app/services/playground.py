from pathlib import Path
import json
from ..utils.command import run_background_process
from ..config import PLAYGROUND_DIR, DUCK_TYPES

# This is going to be where you can load the duck droid models and scenes
# and then use the keyboard to control the duck droid 
# You can also then save the motions as reference motion
# to create and train custom emotes for the droid easily


class PlaygroundService:
    def __init__(self):
        self.process = None
        self.playground_dir = Path(__file__).parent.parent.parent / 'submodules' / 'open_duck_playground'
        self.scenes_dir = self.playground_dir / 'playground' / 'scenes'
        self.tasks = {}

    def test_model(self, duck_type, model_file):
        """Test the trained model in the playground."""
        if duck_type not in DUCK_TYPES:
            raise ValueError(f"Invalid duck type: {duck_type}")

        # Validate model file exists
        model_path = Path(model_file)
        if not model_path.exists():
            raise ValueError(f"Model file not found: {model_file}")

        # Create scene directory if it doesn't exist
        scene_dir = self.scenes_dir / duck_type
        scene_dir.mkdir(parents=True, exist_ok=True)

        # Generate scene configuration
        scene_config = {
            'duck_type': duck_type,
            'model_path': str(model_path),
            'scene_type': 'test',
            'camera': {
                'position': [0, 2, 4],
                'target': [0, 0, 0]
            }
        }

        # Save scene configuration
        scene_file = scene_dir / f"test_{model_path.stem}.json"
        with open(scene_file, "w") as f:
            json.dump(scene_config, f, indent=2)

        # Start playground process
        command = [
            "python", "-m", "playground.main",
            "--scene_file", str(scene_file),
            "--export_glb"
        ]

        self.process = run_background_process(command, cwd=self.playground_dir)
        
        # Store task information
        task_id = str(self.process.pid)
        self.tasks[task_id] = {
            'process': self.process,
            'scene_file': scene_file,
            'status': 'running'
        }

        return {
            'success': True,
            'task_id': task_id,
            'playground_url': f"http://localhost:8000/playground/{task_id}",
            'message': 'Playground started successfully'
        }

    def stop_playground(self):
        """Stop the running playground process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process = None
            return True
        return False

    def is_running(self):
        """Check if the playground process is running."""
        return self.process is not None and self.process.poll() is None

    def get_task_status(self, task_id):
        """Get the status of a playground task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        process = task['process']

        # Check if process is still running
        if process.poll() is None:
            return {
                'status': 'running',
                'playground_url': f"http://localhost:8000/playground/{task_id}"
            }
        else:
            # Process finished
            if process.returncode == 0:
                # Check for GLB file
                glb_file = task['scene_file'].with_suffix('.glb')
                if glb_file.exists():
                    task['status'] = 'completed'
                    return {
                        'status': 'completed',
                        'playground_url': f"http://localhost:8000/playground/{task_id}",
                        'glb_file': str(glb_file)
                    }
                else:
                    task['status'] = 'failed'
                    return {
                        'status': 'failed',
                        'error': 'GLB file not generated'
                    }
            else:
                task['status'] = 'failed'
                return {
                    'status': 'failed',
                    'error': f"Playground failed with return code {process.returncode}"
                } 
