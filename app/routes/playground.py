from flask import Blueprint, render_template, redirect, url_for, jsonify, request
from ..services.playground import PlaygroundService
from ..config import DUCK_TYPES

playground = Blueprint('playground', __name__)
playground_service = PlaygroundService()

@playground.route('/view_playground/<duck_type>')
def view_playground(duck_type):
    """Start the Mujoco playground and render the playground view."""
    if duck_type not in DUCK_TYPES:
        return redirect(url_for('main.index'))
    
    model_path = request.args.get('model')
    if not model_path:
        return redirect(url_for('duck.duck_page', duck_type=duck_type))
    
    # Start playground process
    success, error = playground_service.start_playground(duck_type, model_path)
    if not success:
        return jsonify({'success': False, 'error': error})
    
    return render_template('playground.html',
                         duck_type=duck_type,
                         duck_name=DUCK_TYPES[duck_type],
                         model_name=model_path.split('/')[-1])

@playground.route('/stop_playground', methods=['POST'])
def stop_playground():
    """Stop the running playground process."""
    if playground_service.stop_playground():
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'No playground process running'})

@playground.route('/playground_status')
def playground_status():
    """Check if the playground process is running."""
    return jsonify({
        'running': playground_service.is_running()
    }) 
