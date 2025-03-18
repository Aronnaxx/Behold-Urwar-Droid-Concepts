from ..utils.command import run_command
from ..config import PLAYGROUND_DIR

def generate_motions(duck_type, num_motions=100):
    """Generate reference motions for a specific duck type."""
    if duck_type != 'open_duck_mini_v2':
        return False, 'Motion generation not implemented for this duck type'
    
    # Install placo with C++17 standard
    stdout, stderr = run_command("CXXFLAGS='-std=c++17' pip install placo==0.6.3")
    if stderr:
        return False, f'Failed to install placo: {stderr}'
    
    # Generate motions
    command = f"python scripts/generate_reference_motions.py --num_motions {num_motions}"
    stdout, stderr = run_command(command, cwd=PLAYGROUND_DIR)
    
    if stderr:
        return False, f'Failed to generate motions: {stderr}'
    
    return True, None 
