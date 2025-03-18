from flask import Flask
from pathlib import Path
from .routes.main import main
from .routes.duck import duck
from .routes.training import training
from .routes.playground import playground
from .routes.open_duck_mini import open_duck_mini
from .config import OUTPUT_DIR, TRAINED_MODELS_DIR, DUCK_TYPES

def create_app():
    """Create and configure the Flask application."""
    # Get the root directory (where templates are located)
    root_dir = Path(__file__).parent.parent
    app = Flask(__name__, 
                template_folder=str(root_dir / 'templates'),
                static_folder=str(root_dir / 'static'))
    
    # Add datetime filter
    @app.template_filter('datetime')
    def format_datetime(value):
        """Format a datetime object."""
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        return str(value)
    
    # Create necessary directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    TRAINED_MODELS_DIR.mkdir(exist_ok=True)
    for duck_type in DUCK_TYPES:
        (TRAINED_MODELS_DIR / duck_type).mkdir(exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(duck)
    app.register_blueprint(training)
    app.register_blueprint(playground)
    app.register_blueprint(open_duck_mini)
    
    return app 
