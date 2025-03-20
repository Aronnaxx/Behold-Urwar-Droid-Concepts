from pathlib import Path
from ..utils.command import run_command
from ..config import PLAYGROUND_DIR, OUTPUT_DIR, DUCK_TYPES

class MotionService:
    def __init__(self):
        self.motion_generator_dir = Path(__file__).parent.parent.parent / 'submodules' / 'open_duck_reference_motion_generator'
        self.output_dir = OUTPUT_DIR / 'motions'
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.playground_dir = Path(__file__).parent.parent.parent / 'submodules' / 'open_duck_playground'

    def generate_motion(self, duck_type, motion_params):
        """Generate a reference motion for a specific duck type."""
        if duck_type not in DUCK_TYPES:
            raise ValueError(f"Invalid duck type: {duck_type}")

        # Validate motion parameters
        if not self._validate_motion_params(motion_params):
            raise ValueError("Invalid motion parameters")

        # Generate unique output filename
        output_file = self.output_dir / f"{duck_type}_{motion_params['motion_type']}_{motion_params.get('speed', 'default')}.json"

        # Build command with parameters
        command = [
            "uv", "run", "scripts/auto_waddle.py",
            "--duck", duck_type,
            "--output_dir", str(self.output_dir)
        ]

        # Add optional parameters
        if motion_params.get('num_motions'):
            command.extend(["--num", str(motion_params['num_motions'])])
        elif motion_params.get('sweep'):
            command.append("--sweep")

        # Run command
        stdout, stderr = run_command(command, cwd=self.motion_generator_dir)
        
        if stderr:
            raise RuntimeError(f"Failed to generate motion: {stderr}")

        # Fit polynomials to the generated motion
        self._fit_polynomials(output_file)

        return {
            'success': True,
            'motion_file': str(output_file),
            'message': 'Motion generated and polynomials fitted successfully'
        }

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

# Create a singleton instance
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