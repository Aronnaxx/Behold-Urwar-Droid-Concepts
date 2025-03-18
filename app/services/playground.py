from ..utils.command import run_background_process
from ..config import PLAYGROUND_DIR

class PlaygroundService:
    def __init__(self):
        self.process = None
    
    def start_playground(self, duck_type, model_path):
        """Start the Mujoco playground with a specific model."""
        if duck_type != 'open_duck_mini_v2':
            return False, 'Playground not implemented for this duck type'
        
        if not model_path:
            return False, 'Model path is required'
        
        # Start playground process
        command = f"python scripts/playground.py --model_path {model_path}"
        self.process = run_background_process(command, cwd=PLAYGROUND_DIR)
        
        return True, None
    
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
