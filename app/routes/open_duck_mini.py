from flask import Blueprint, request, jsonify, render_template
import subprocess
import os
from pathlib import Path

# Create blueprint with URL prefix
open_duck_mini = Blueprint('open_duck_mini', __name__, url_prefix='/open_duck_mini')

def run_command(command, cwd):
    """
    Helper function to run a shell command in the given directory.
    Returns a tuple (stdout, stderr).
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

@open_duck_mini.route('/')
def open_duck_mini_page():
    """Render the Open Duck Mini page."""
    return render_template('open_duck_mini.html')

@open_duck_mini.route('/reference-motions')
def reference_motions():
    """Render the reference motion generation page."""
    return render_template('reference_motions.html')

@open_duck_mini.route('/setup', methods=['POST'])
def setup():
    """
    Endpoint to run the setup for Open Duck Mini.
    """
    try:
        # Install the Open Duck Playground package
        playground_cwd = os.path.join(os.getcwd(), 'submodules', 'open_duck_playground')
        reference_motion_cwd = os.path.join(os.getcwd(), 'submodules', 'open_duck_reference_motion_generator')
        
        # Check if directories exist
        if not os.path.exists(playground_cwd) or not os.path.exists(reference_motion_cwd):
            return jsonify({
                'success': False, 
                'error': f'One or more required directories not found:\n{playground_cwd}\n{reference_motion_cwd}'
            }), 500

        # Install the Open Duck Playground package
        stdout, stderr = run_command("pip install -e . -v", playground_cwd)
        
        # Install the Open Duck Reference Motion Generator package
        stdout, stderr = run_command("pip install -e . -v", reference_motion_cwd)
        
        # Check installation success - look for both package name formats
        verify_stdout, verify_stderr = run_command("pip show Open-Duck-Playground", playground_cwd)
        if "Name: Open-Duck-Playground" not in verify_stdout and "Name: Open_Duck_Playground" not in verify_stdout:
            return jsonify({
                'success': False,
                'error': f'Installation verification failed.\nStdout: {stdout}\nStderr: {stderr}'
            }), 500
            
        return jsonify({
            'success': True,
            'output': f'Installation successful.\nStdout: {stdout}\nStderr: {stderr}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Setup failed with error: {str(e)}'
        }), 500

@open_duck_mini.route('/launch', methods=['POST'])
def launch():
    """
    Endpoint to launch the Open Duck Mini gait playground.
    """
    cwd = os.path.join(os.getcwd(), 'submodules', 'open_duck_reference_motion_generator')
    
    # Add the playground directory to PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = f"{cwd}:{env.get('PYTHONPATH', '')}"
    
    try:
        # First check if the process is already running
        ps_result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        if "gait_playground.py" in ps_result.stdout:
            return jsonify({
                'success': False,
                'error': 'Application is already running. Please close it before launching again.'
            }), 400

        # Launch the application with debug output
        result = subprocess.Popen(
            ["python", "-u", "open_duck_reference_motion_generator/gait_playground.py", "--duck", "open_duck_mini_v2"],
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Read initial output to check for immediate errors
        try:
            stdout, stderr = result.communicate(timeout=5)
            if result.returncode is not None and result.returncode != 0:
                return jsonify({
                    'success': False,
                    'error': f'Application failed to start:\n{stderr}'
                }), 500
                
            return jsonify({
                'success': True,
                'output': f'Application launched successfully.\nOutput: {stdout}\nErrors: {stderr}'
            })
            
        except subprocess.TimeoutExpired:
            # Process is still running (good!)
            result.kill()  # Kill the process we used for checking
            return jsonify({
                'success': True,
                'output': 'Application launched successfully and is running in the background.'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Launch failed with error: {str(e)}'
        }), 500

@open_duck_mini.route('/status', methods=['GET'])
def status():
    """
    Endpoint to check the status of Open Duck Mini setup and running processes.
    """
    playground_cwd = os.path.join(os.getcwd(), 'submodules', 'open_duck_reference_motion_generator')
    
    # Check if the package is installed - look for both package name formats
    stdout, _ = run_command("pip show Open-Duck-Playground", playground_cwd)
    if "Name: Open-Duck-Playground" not in stdout:
        stdout, _ = run_command("pip show Open_Duck_Playground", playground_cwd)
    playground_installed = "Name: Open-Duck-Playground" in stdout or "Name: Open_Duck_Playground" in stdout
    
    # Check if the gait playground file exists
    playground_file = Path(playground_cwd) / 'open_duck_reference_motion_generator' / 'gait_playground.py'
    
    return jsonify({
        'setup_file_exists': playground_installed,
        'main_file_exists': playground_file.exists(),
        'directory_exists': os.path.exists(playground_cwd)
    }) 
