from flask import Blueprint, render_template, request, jsonify
from ..services.motion import MotionService
from ..services.training import TrainingService
from ..services.playground import PlaygroundService
from ..config import DUCK_TYPES

workflow = Blueprint('workflow', __name__)
motion_service = MotionService()
training_service = TrainingService()
playground_service = PlaygroundService()

@workflow.route('/')
def workflow_page():
    """Render the main workflow page."""
    return render_template('workflow/index.html', duck_types=DUCK_TYPES)

@workflow.route('/generate_motion', methods=['POST'])
def generate_motion():
    """Generate a reference motion."""
    try:
        data = request.get_json()
        duck_type = data.get('duck_type')
        motion_params = data.get('motion_params', {})
        
        if duck_type not in DUCK_TYPES:
            return jsonify({'success': False, 'error': 'Invalid duck type'})
        
        result = motion_service.generate_motion(duck_type, motion_params)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow.route('/train', methods=['POST'])
def train():
    """Train a policy using the generated motion."""
    try:
        data = request.get_json()
        duck_type = data.get('duck_type')
        motion_file = data.get('motion_file')
        training_params = data.get('training_params', {})
        
        if duck_type not in DUCK_TYPES:
            return jsonify({'success': False, 'error': 'Invalid duck type'})
        
        result = training_service.train(duck_type, motion_file, training_params)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow.route('/test', methods=['POST'])
def test():
    """Test the trained model in the playground."""
    try:
        data = request.get_json()
        duck_type = data.get('duck_type')
        model_file = data.get('model_file')
        
        if duck_type not in DUCK_TYPES:
            return jsonify({'success': False, 'error': 'Invalid duck type'})
        
        result = playground_service.test_model(duck_type, model_file)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@workflow.route('/status/<task_id>')
def get_status(task_id):
    """Get the status of a running task."""
    try:
        status = motion_service.get_task_status(task_id)
        if not status:
            status = training_service.get_task_status(task_id)
        if not status:
            status = playground_service.get_task_status(task_id)
            
        if not status:
            return jsonify({'success': False, 'error': 'Task not found'})
            
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 