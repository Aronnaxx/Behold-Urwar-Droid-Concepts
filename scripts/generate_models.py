#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

def find_robot_files():
    """Find all URDF and MJCF files in the submodules directory."""
    robot_files = []
    submodules_dir = Path('submodules')
    
    for root, dirs, files in os.walk(submodules_dir):
        for file in files:
            if file.endswith(('.urdf', '.xml')):  # .xml for MJCF files
                robot_files.append(Path(root) / file)
    
    return robot_files

def convert_to_glb(input_file, output_dir):
    """Convert URDF/MJCF file to GLB format."""
    # Parse file to get robot name
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    # Handle both URDF and MJCF files
    if root.tag == 'robot':  # URDF
        robot_name = root.get('name', 'robot')
    else:  # MJCF
        robot_name = input_file.stem
    
    # Create output directory if it doesn't exist
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{robot_name}.glb"
    
    # Use blender to convert the file (this assumes Blender is installed)
    blender_script = f"""
import bpy
import os

# Clear existing objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import URDF/MJCF
if '{input_file}'.endswith('.urdf'):
    bpy.ops.import_mesh.urdf(filepath='{input_file}')
else:
    bpy.ops.import_mesh.mujoco(filepath='{input_file}')

# Export as GLB
bpy.ops.export_scene.gltf(
    filepath='{output_file}',
    export_format='GLB',
    use_selection=False
)
"""
    
    with open('convert.py', 'w') as f:
        f.write(blender_script)
    
    subprocess.run(['blender', '--background', '--python', 'convert.py'], check=True)
    os.remove('convert.py')
    
    return output_file

def main():
    # Find all robot files
    robot_files = find_robot_files()
    
    # Convert each file to GLB
    output_dir = Path('static/models')
    for robot_file in robot_files:
        try:
            print(f"Converting {robot_file}...")
            glb_file = convert_to_glb(robot_file, output_dir)
            print(f"Created {glb_file}")
        except Exception as e:
            print(f"Error converting {robot_file}: {e}")

if __name__ == '__main__':
    main() 
