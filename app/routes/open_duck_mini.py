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
    cwd = os.path.join(os.getcwd(), 'submodules', 'open_duck_mini')
    
    # Install the package in development mode
    stdout, stderr = run_command("pip install -e .", cwd)
    
    if stderr and "Successfully installed" not in stderr:
        return jsonify({'success': False, 'error': stderr}), 500
    return jsonify({'success': True, 'output': stdout})

@open_duck_mini.route('/launch', methods=['POST'])
def launch():
    """
    Endpoint to launch the Open Duck Mini playground.
    """
    cwd = os.path.join(os.getcwd(), 'submodules', 'open_duck_playground')
    stdout, stderr = run_command("python playground/open_duck_mini_v2/runner.py --env joystick --task walk", cwd)
    
    if stderr:
        return jsonify({'success': False, 'error': stderr}), 500
    return jsonify({'success': True, 'output': stdout})

@open_duck_mini.route('/status', methods=['GET'])
def status():
    """
    Endpoint to check the status of Open Duck Mini setup and running processes.
    """
    cwd = os.path.join(os.getcwd(), 'submodules', 'open_duck_mini')
    playground_dir = os.path.join(os.getcwd(), 'submodules', 'open_duck_playground')
    
    # Check if the package is installed
    stdout, stderr = run_command("pip show mini-bdx", cwd)
    package_installed = "Name: mini-bdx" in stdout
    
    # Check if the playground runner exists
    runner_file = Path(playground_dir) / 'playground' / 'open_duck_mini_v2' / 'runner.py'
    
    return jsonify({
        'setup_file_exists': package_installed,
        'main_file_exists': runner_file.exists(),
        'directory_exists': os.path.exists(cwd)
    }) 
