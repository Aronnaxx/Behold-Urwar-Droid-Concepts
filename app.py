from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Add datetime filter
@app.template_filter('datetime')
def format_datetime(value):
    """Format a datetime object."""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return str(value)

# Configuration
DUCK_TYPES = {
    'bdx': 'BDX Duck',
    'open_duck_mini_v2': 'Open Duck Mini V2'
}

OUTPUT_DIR = Path('generated_motions')
PLAYGROUND_DIR = Path('submodules/open_duck_playground')
REFERENCE_MOTION_DIR = Path('submodules/open_duck_playground/open_duck_mini_v2/data')
AWD_DIR = Path('submodules/awd')
TRAINED_MODELS_DIR = Path('trained_models')

# Store playground process
playground_process = None

def run_command(command, cwd=None):
    """Run a shell command and return its output."""
    print(f"Running command: {command}")
    print(f"Working directory: {cwd or os.getcwd()}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True
        )
        print(f"Command output: {result.stdout}")
        if result.stderr:
            print(f"Command error: {result.stderr}")
        return result.stdout, result.stderr
    except Exception as e:
        print(f"Command error: {str(e)}")
        return None, str(e)

def get_trained_models(duck_type):
    """Get list of trained models for a specific duck type."""
    models_dir = TRAINED_MODELS_DIR / duck_type
    if not models_dir.exists():
        return []
    
    models = []
    for model_file in models_dir.glob('*.onnx'):
        models.append({
            'name': model_file.name,
            'path': str(model_file),
            'date': datetime.fromtimestamp(model_file.stat().st_mtime)
        })
    return sorted(models, key=lambda x: x['date'], reverse=True)

@app.route('/')
def index():
    """Render the main dashboard with available duck types."""
    return render_template('index.html', duck_types=DUCK_TYPES)

@app.route('/<duck_type>')
def duck_page(duck_type):
    """Render the page for a specific duck type."""
    if duck_type not in DUCK_TYPES:
        return redirect(url_for('index'))
    
    trained_models = get_trained_models(duck_type)
    return render_template('duck_page.html', 
                         duck_type=duck_type,
                         duck_name=DUCK_TYPES[duck_type],
                         trained_models=trained_models)

@app.route('/generate_motions', methods=['POST'])
def generate_motions():
    """Generate reference motions for a specific duck type."""
    data = request.get_json()
    duck_type = data.get('duck_type')
    num_motions = data.get('num_motions', 100)
    
    if duck_type not in DUCK_TYPES:
        return jsonify({'success': False, 'error': 'Invalid duck type'})
    
    # Install placo with C++17 standard
    stdout, stderr = run_command("CXXFLAGS='-std=c++17' pip install placo==0.6.3")
    if stderr:
        return jsonify({'success': False, 'error': f'Failed to install placo: {stderr}'})
    
    # Generate motions
    if duck_type == 'open_duck_mini_v2':
        command = f"python scripts/generate_reference_motions.py --num_motions {num_motions}"
        cwd = PLAYGROUND_DIR
    else:
        return jsonify({'success': False, 'error': 'Motion generation not implemented for this duck type'})
    
    stdout, stderr = run_command(command, cwd)
    if stderr:
        return jsonify({'success': False, 'error': f'Failed to generate motions: {stderr}'})
    
    return jsonify({'success': True})

@app.route('/train', methods=['POST'])
def train():
    """Start training for a specific duck type."""
    data = request.get_json()
    duck_type = data.get('duck_type')
    training_options = data.get('training_options', {})
    
    if duck_type not in DUCK_TYPES:
        return jsonify({'success': False, 'error': 'Invalid duck type'})
    
    # Start training process
    if duck_type == 'open_duck_mini_v2':
        command = "python scripts/train.py"
        if training_options.get('use_imitation_reward'):
            command += " --use_imitation_reward"
        if training_options.get('num_envs'):
            command += f" --num_envs {training_options['num_envs']}"
        cwd = PLAYGROUND_DIR
    else:
        return jsonify({'success': False, 'error': 'Training not implemented for this duck type'})
    
    # Run training in background
    process = subprocess.Popen(
        command,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    return jsonify({'success': True, 'pid': process.pid})

@app.route('/infer', methods=['POST'])
def infer():
    """Run inference with a trained model."""
    data = request.get_json()
    duck_type = data.get('duck_type')
    model_path = data.get('model_path')
    
    if duck_type not in DUCK_TYPES:
        return jsonify({'success': False, 'error': 'Invalid duck type'})
    
    if not os.path.exists(model_path):
        return jsonify({'success': False, 'error': 'Model file not found'})
    
    # Run inference
    if duck_type == 'open_duck_mini_v2':
        command = f"python scripts/infer.py --model_path {model_path}"
        cwd = PLAYGROUND_DIR
    else:
        return jsonify({'success': False, 'error': 'Inference not implemented for this duck type'})
    
    stdout, stderr = run_command(command, cwd)
    if stderr:
        return jsonify({'success': False, 'error': f'Failed to run inference: {stderr}'})
    
    return jsonify({'success': True})

@app.route('/view_playground/<duck_type>')
def view_playground(duck_type):
    """Start the Mujoco playground and render the playground view."""
    if duck_type not in DUCK_TYPES:
        return redirect(url_for('index'))
    
    model_path = request.args.get('model')
    if not model_path or not os.path.exists(model_path):
        return redirect(url_for('duck_page', duck_type=duck_type))
    
    # Start playground process
    global playground_process
    if playground_process is None or playground_process.poll() is not None:
        if duck_type == 'open_duck_mini_v2':
            command = f"python scripts/playground.py --model_path {model_path}"
            cwd = PLAYGROUND_DIR
        else:
            return jsonify({'success': False, 'error': 'Playground not implemented for this duck type'})
        
        playground_process = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    
    return render_template('playground.html',
                         duck_type=duck_type,
                         duck_name=DUCK_TYPES[duck_type],
                         model_name=os.path.basename(model_path))

@app.route('/stop_playground', methods=['POST'])
def stop_playground():
    """Stop the running playground process."""
    global playground_process
    if playground_process and playground_process.poll() is None:
        playground_process.terminate()
        playground_process = None
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No playground process running'})

@app.route('/playground_status')
def playground_status():
    """Check if the playground process is running."""
    global playground_process
    return jsonify({
        'running': playground_process is not None and playground_process.poll() is None
    })

@app.route('/status')
def status():
    """Get the current status of the system."""
    return jsonify({
        'training_running': False,  # TODO: Implement training status check
        'generated_motions': OUTPUT_DIR.exists() and any(OUTPUT_DIR.iterdir()),
        'playground_ready': playground_process is not None and playground_process.poll() is None
    })

if __name__ == '__main__':
    # Create necessary directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    TRAINED_MODELS_DIR.mkdir(exist_ok=True)
    for duck_type in DUCK_TYPES:
        (TRAINED_MODELS_DIR / duck_type).mkdir(exist_ok=True)
    
    app.run(debug=True) 
