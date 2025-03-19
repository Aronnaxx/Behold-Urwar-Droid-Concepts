from ..utils.command import run_background_process
from ..config import PLAYGROUND_DIR

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
