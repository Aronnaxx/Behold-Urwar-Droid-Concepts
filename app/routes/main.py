from flask import Blueprint, render_template, redirect, url_for
from ..config import duck_config, LEARNING_CONTENT

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Render the main dashboard with available duck types."""
    return render_template('index.html', duck_types=duck_config.get_duck_types())

@main.route('/learn/<topic>')
def learn(topic):
    """Render the learning center page for a specific topic."""
    if topic not in LEARNING_CONTENT:
        return redirect(url_for('main.index'))
    
    content = LEARNING_CONTENT[topic]
    return render_template('learn.html',
                         title=content['title'],
                         model_path=content['model_path'],
                         overview=content['overview'],
                         how_it_works=content['how_it_works'],
                         examples=content['examples'],
                         key_concepts=content['key_concepts'],
                         resources=content['resources']) 
