from ..utils.command import run_background_process
from ..config import PLAYGROUND_DIR

def start_training(duck_type, training_options=None):
    """Start training for a specific duck type."""
    if duck_type != 'open_duck_mini_v2':
        return False, 'Training not implemented for this duck type'
    
    # Build training command
    command = "python scripts/train.py"
    if training_options:
        if training_options.get('use_imitation_reward'):
            command += " --use_imitation_reward"
        if training_options.get('num_envs'):
            command += f" --num_envs {training_options['num_envs']}"
    
    # Start training process
    process = run_background_process(command, cwd=PLAYGROUND_DIR)
    
    return True, process.pid 
