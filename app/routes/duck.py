from flask import Blueprint, render_template, redirect, url_for, jsonify
from datetime import datetime
from pathlib import Path
from ..config import DUCK_TYPES, TRAINED_MODELS_DIR

duck = Blueprint('duck', __name__)

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

@duck.route('/<duck_type>')
def duck_page(duck_type):
    """Render the page for a specific duck type."""
    if duck_type not in DUCK_TYPES:
        return redirect(url_for('main.index'))
    
    # Create a duck object with all necessary information
    duck_data = {
        'name': DUCK_TYPES[duck_type],
        'type': duck_type,
        'model_path': f'/static/models/{duck_type}.glb',  # Path to 3D model
        'description': f'Details and information about the {DUCK_TYPES[duck_type]} duck.',
        'features': [
            'Advanced walking dynamics',
            'Real-time motion planning',
            'Terrain adaptation',
            'Energy optimization'
        ],
        'specifications': [
            {'title': 'Height', 'value': '1.2m'},
            {'title': 'Weight', 'value': '5kg'},
            {'title': 'Battery Life', 'value': '4 hours'}
        ],
        'resources': [
            {
                'title': 'Training Guide',
                'description': 'Learn how to train your own model',
                'url': url_for('main.learn', topic='training')
            },
            {
                'title': 'Playground',
                'description': 'Test and experiment with the duck',
                'url': url_for('playground.view_playground', duck_type=duck_type)
            }
        ]
    }
    
    trained_models = get_trained_models(duck_type)
    return render_template('duck_page.html', 
                         duck=duck_data,
                         trained_models=trained_models) 
