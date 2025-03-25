import trimesh
from pathlib import Path
import logging
from typing import List, Dict, Tuple
from ..config import duck_config, ROOT_DIR

logger = logging.getLogger(__name__)

def convert_stl_to_glb(input_path: str, output_path: str) -> Tuple[bool, str]:
    """
    Convert a single STL file to GLB format.
    
    Args:
        input_path: Path to the input STL file
        output_path: Path where the GLB file should be saved
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        mesh = trimesh.load(input_path)
        mesh.export(output_path, file_type='glb')
        logger.info(f"Successfully converted {input_path} to {output_path}")
        return True, f"Converted {input_path} to {output_path}"
    except Exception as e:
        error_msg = f"Error converting {input_path} to GLB: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def convert_stl_directory(input_dir: str, output_dir: str) -> Dict[str, Tuple[bool, str]]:
    """
    Convert all STL files in a directory to GLB format.
    
    Args:
        input_dir: Directory containing STL files
        output_dir: Directory where GLB files should be saved
        
    Returns:
        Dictionary mapping filenames to (success, message) tuples
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    results = {}
    for stl_file in input_path.glob("*.stl"):
        glb_file = output_path / f"{stl_file.stem}.glb"
        success, message = convert_stl_to_glb(str(stl_file), str(glb_file))
        results[stl_file.name] = (success, message)
    
    return results

def get_stl_and_glb_files(duck_type: str, variant: str = None) -> Dict[str, List[Dict]]:
    """
    Get lists of STL and GLB files for a specific duck type and variant.
    Automatically converts STL to GLB if needed.
    
    Args:
        duck_type: Type of duck (e.g., 'open_duck_mini')
        variant: Optional variant name
        
    Returns:
        Dictionary containing lists of STL and GLB file information
    """
    # Get duck type config
    duck_config_data = duck_config.get_duck_type(duck_type)
    if not duck_config_data:
        logger.error(f"Invalid duck type: {duck_type}")
        return {'stl_files': [], 'glb_files': []}
    
    # Get STL directory from config or use default
    stl_dir = Path(duck_config_data.get('stl_directory', ROOT_DIR / 'submodules/open_duck_mini/print'))
    if not stl_dir.is_absolute():
        stl_dir = Path(__file__).parent.parent.parent / stl_dir
    
    # Construct GLB directory path
    glb_dir = ROOT_DIR / "app" / "static" / "models" / duck_type
    if variant:
        glb_dir = glb_dir / variant
    
    # Create GLB directory if it doesn't exist
    glb_dir.mkdir(parents=True, exist_ok=True)
    
    # Get STL files
    stl_files = []
    for stl_file in stl_dir.glob("*.stl"):
        stl_files.append({
            'name': stl_file.name,
            'path': str(stl_file),
            'size': stl_file.stat().st_size,
            'modified': stl_file.stat().st_mtime
        })
    
    # Get GLB files
    glb_files = []
    for glb_file in glb_dir.glob("*.glb"):
        glb_files.append({
            'name': glb_file.name,
            'path': str(glb_file),
            'size': glb_file.stat().st_size,
            'modified': glb_file.stat().st_mtime
        })
    
    # If we have STL files but no GLB files, convert them
    if stl_files and not glb_files:
        logger.info(f"No GLB files found for {duck_type}, converting STL files...")
        results = convert_stl_directory(str(stl_dir), str(glb_dir))
        
        # Check for any failed conversions
        failed_files = [name for name, (success, _) in results.items() if not success]
        if failed_files:
            logger.error(f"Failed to convert some files: {failed_files}")
        else:
            # Reload GLB files after conversion
            glb_files = []
            for glb_file in glb_dir.glob("*.glb"):
                glb_files.append({
                    'name': glb_file.name,
                    'path': str(glb_file),
                    'size': glb_file.stat().st_size,
                    'modified': glb_file.stat().st_mtime
                })
    
    return {
        'stl_files': sorted(stl_files, key=lambda x: x['name']),
        'glb_files': sorted(glb_files, key=lambda x: x['name'])
    }
