from pathlib import Path
import json
from ..utils.command import run_background_process
from ..config import PLAYGROUND_DIR, TRAINED_MODELS_DIR, DUCK_TYPES

# TODO: Add training options
# This will be the endpoints for the training options of the duck droids
# basically, from the web frontend, you send a request to this endpoint with the training options
# and then this endpoint will start the training process
# the training process will be a background process

# Once training is done, the endpoint will return the training results
# and the frontend will display the training results through the duck droid visualization

# The user will need to choose the duck type, the simulation environment, and the parameters.

# TODO is include the model and the scenes, and once the training is complete, convert the scene to a glb that can 
# be used in the frontend

class TrainingService:
    def __init__(self):
        self.playground_dir = Path(__file__).parent.parent.parent / 'submodules' / 'open_duck_playground'
        self.tasks = {}

    def train(self, duck_type, training_options=None):
        """Start training for a specific duck type."""
        if duck_type not in DUCK_TYPES:
            raise ValueError(f"Invalid duck type: {duck_type}")

        # Validate training options
        if not self._validate_training_options(training_options):
            raise ValueError("Invalid training options")

        # Create output directory
        output_dir = TRAINED_MODELS_DIR / duck_type
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save training parameters
        if training_options:
            params_file = output_dir / "training_params.json"
            with open(params_file, "w") as f:
                json.dump(training_options, f, indent=2)

        # Build training command
        command = [
            "uv", "run", "playground/open_duck_mini_v2/runner.py",
            "--output_dir", str(output_dir)
        ]

        # Add training options
        if training_options:
            if training_options.get('num_envs'):
                command.extend(["--num_envs", str(training_options['num_envs'])])
            if training_options.get('total_timesteps'):
                command.extend(["--total_timesteps", str(training_options['total_timesteps'])])

        # Start training process
        process = run_background_process(command, cwd=self.playground_dir)
        
        # Store task information
        task_id = str(process.pid)
        self.tasks[task_id] = {
            'process': process,
            'output_dir': output_dir,
            'status': 'running'
        }

        return {
            'success': True,
            'task_id': task_id,
            'message': 'Training started successfully'
        }

    def _validate_training_options(self, options):
        """Validate training options."""
        if not options:
            return True

        if options.get('num_envs'):
            try:
                num = int(options['num_envs'])
                if not 1 <= num <= 128:
                    return False
            except ValueError:
                return False

        if options.get('total_timesteps'):
            try:
                steps = int(options['total_timesteps'])
                if not 1000000 <= steps <= 1000000000:
                    return False
            except ValueError:
                return False

        return True

    def get_task_status(self, task_id):
        """Get the status of a training task."""
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]
        process = task['process']

        # Check if process is still running
        if process.poll() is None:
            # Calculate progress from training logs
            progress = self._calculate_training_progress(task['output_dir'])
            return {
                'status': 'running',
                'progress': progress
            }
        else:
            # Process finished
            if process.returncode == 0:
                task['status'] = 'completed'
                return {
                    'status': 'completed',
                    'output_dir': str(task['output_dir'])
                }
            else:
                task['status'] = 'failed'
                return {
                    'status': 'failed',
                    'error': f"Training failed with return code {process.returncode}"
                }

    def _calculate_training_progress(self, output_dir):
        """Calculate training progress from logs."""
        # Look for progress file or log file
        progress_file = output_dir / "progress.json"
        if progress_file.exists():
            try:
                with open(progress_file) as f:
                    progress = json.load(f)
                    return progress.get('progress', 0)
            except:
                pass
        return 0 
