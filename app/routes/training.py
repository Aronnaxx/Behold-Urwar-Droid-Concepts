from flask import Blueprint, jsonify, request
from ..services.motion import generate_motions
from ..services.training import training_service
from ..config import DUCK_TYPES

training = Blueprint('training', __name__)

@training.route('/generate_motions', methods=['POST'])
def generate_motions_route():
    """Generate reference motions for a specific duck type."""
    data = request.get_json()
    duck_type = data.get('duck_type')
    num_motions = data.get('num_motions', 100)
    
    if duck_type not in DUCK_TYPES:
        return jsonify({'success': False, 'error': 'Invalid duck type'})
    
    try:
        result = generate_motions(duck_type, num_motions)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@training.route('/train', methods=['POST'])
def train_route():
    """Start training for a specific duck type."""
    data = request.get_json()
    duck_type = data.get('duck_type')
    training_options = data.get('training_options', {})
    
    if duck_type not in DUCK_TYPES:
        return jsonify({'success': False, 'error': 'Invalid duck type'})
    
    success, result = training_service.start_training(duck_type, training_options)
    if not success:
        return jsonify({'success': False, 'error': result})
    
    return jsonify({'success': True, 'task_id': result}) 
