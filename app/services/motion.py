import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from ..utils.command import run_command
from ..config import PLAYGROUND_DIR, OUTPUT_DIR, DUCK_TYPES

class MotionService:
    def __init__(self):
        self.motions_dir = Path('data/motions')
        self.motions_dir.mkdir(parents=True, exist_ok=True)
        self.motion_generator_dir = Path(__file__).parent.parent.parent / 'submodules' / 'open_duck_reference_motion_generator'
        self.output_dir = OUTPUT_DIR / 'motions'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.playground_dir = Path(__file__).parent.parent.parent / 'submodules' / 'open_duck_playground'

    def generate_motion(self, duck_type, motion_params):
        """Generate a reference motion for the specified duck type."""
        try:
            # Create a unique ID for this motion
            motion_id = str(uuid.uuid4())
            
            # Create motion directory
            motion_dir = self.motions_dir / duck_type / motion_id
            motion_dir.mkdir(parents=True, exist_ok=True)
            
            # Save motion parameters
            params_file = motion_dir / 'params.json'
            with open(params_file, 'w') as f:
                json.dump(motion_params, f, indent=2)
                
            # Generate motion based on type
            if motion_params['type'] == 'walk':
                self._generate_walking_motion(motion_dir, motion_params)
            else:
                raise ValueError(f"Unsupported motion type: {motion_params['type']}")
                
            return motion_id
            
        except Exception as e:
            print(f"Error generating motion: {str(e)}")
            return None
            
    def _generate_walking_motion(self, motion_dir, params):
        """Generate a walking motion using the specified parameters."""
        try:
            # Import required modules
            from submodules.open_duck_reference_motion_generator.reference_motion_generator import PolyReferenceMotion
            
            # Create motion generator
            motion_generator = PolyReferenceMotion(
                speed=params['speed'],
                duration=params['duration'],
                stride_length=params['stride_length']
            )
            
            # Generate motion data
            motion_data = motion_generator.generate()
            
            # Save motion data
            motion_file = motion_dir / 'motion.json'
            with open(motion_file, 'w') as f:
                json.dump(motion_data, f, indent=2)
                
        except Exception as e:
            print(f"Error generating walking motion: {str(e)}")
            raise
            
    def get_motion(self, duck_type, motion_id):
        """Get motion data by ID."""
        try:
            motion_dir = self.motions_dir / duck_type / motion_id
            if not motion_dir.exists():
                return None
                
            # Load motion data
            motion_file = motion_dir / 'motion.json'
            if not motion_file.exists():
                return None
                
            with open(motion_file, 'r') as f:
                motion_data = json.load(f)
                
            # Load parameters
            params_file = motion_dir / 'params.json'
            if params_file.exists():
                with open(params_file, 'r') as f:
                    params = json.load(f)
            else:
                params = {}
                
            return {
                'id': motion_id,
                'data': motion_data,
                'params': params,
                'created_at': datetime.fromtimestamp(motion_file.stat().st_mtime).isoformat()
            }
            
        except Exception as e:
            print(f"Error getting motion: {str(e)}")
            return None
            
    def list_motions(self, duck_type):
        """List all motions for a duck type."""
        try:
            duck_dir = self.motions_dir / duck_type
            if not duck_dir.exists():
                return []
                
            motions = []
            for motion_id in duck_dir.iterdir():
                if motion_id.is_dir():
                    motion = self.get_motion(duck_type, motion_id.name)
                    if motion:
                        motions.append(motion)
                        
            return sorted(motions, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            print(f"Error listing motions: {str(e)}")
            return []
            
    def delete_motion(self, duck_type, motion_id):
        """Delete a motion by ID."""
        try:
            motion_dir = self.motions_dir / duck_type / motion_id
            if motion_dir.exists():
                import shutil
                shutil.rmtree(motion_dir)
                return True
            return False
            
        except Exception as e:
            print(f"Error deleting motion: {str(e)}")
            return False

    def _fit_polynomials(self, motion_file):
        """Fit polynomials to the reference motion and copy to playground."""
        # Fit polynomials
        command = [
            "uv", "run", "scripts/fit_poly.py",
            "--ref_motion", str(motion_file)
        ]
        stdout, stderr = run_command(command, cwd=self.motion_generator_dir)
        
        if stderr:
            raise RuntimeError(f"Failed to fit polynomials: {stderr}")

        # Copy polynomial coefficients to playground
        coeff_file = self.motion_generator_dir / "polynomial_coefficients.pkl"
        if not coeff_file.exists():
            raise RuntimeError("Polynomial coefficients file not generated")

        # Copy to playground data directory
        playground_data_dir = self.playground_dir / "playground" / "open_duck_mini_v2" / "data"
        playground_data_dir.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy2(coeff_file, playground_data_dir / "polynomial_coefficients.pkl")

    def _validate_motion_params(self, params):
        """Validate motion parameters."""
        required = ['motion_type']
        if not all(k in params for k in required):
            return False

        if params['motion_type'] not in ['walk', 'custom']:
            return False

        # Validate sweep or num_motions is provided
        if not (params.get('sweep') or params.get('num_motions')):
            return False

        if params.get('num_motions'):
            try:
                num = int(params['num_motions'])
                if not 1 <= num <= 1000:
                    return False
            except ValueError:
                return False

        return True

    def get_task_status(self, task_id):
        """Get the status of a motion generation task."""
        # Since motion generation is synchronous, we don't need to track task status
        return None

# Create singleton instance
motion_service = MotionService()

def generate_motions(duck_type, num_motions=100):
    """Generate reference motions for a specific duck type.
    
    Args:
        duck_type (str): Type of duck to generate motions for
        num_motions (int, optional): Number of motions to generate. Defaults to 100.
    
    Returns:
        dict: Result containing success status, motion file path, and message
    """
    return motion_service.generate_motion(duck_type, {
        'motion_type': 'walk',
        'num_motions': num_motions
    })

# Export the function and service
__all__ = ['generate_motions', 'motion_service'] 