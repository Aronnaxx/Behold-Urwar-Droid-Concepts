from flask import Flask
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
from .config import Config, OUTPUT_DIR, TRAINED_MODELS_DIR, DUCK_TYPES
from .routes.main import main
from .routes.duck import DuckBlueprint
from .routes.routes import DuckRoutes
import logging

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    # Get the root directory (where templates are located)
    root_dir = Path(__file__).parent.parent
    app = Flask(__name__, 
                template_folder=str(root_dir / 'templates'),
                static_folder=str(root_dir / 'static'))
    
    CORS(app)
    app.config.from_object(config_class)
    
    # Set the port
    app.config['SERVER_NAME'] = f'127.0.0.1:{app.config["PORT"]}'
    
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
    for duck_type, info in DUCK_TYPES.items():
        duck_dir = TRAINED_MODELS_DIR / duck_type
        duck_dir.mkdir(exist_ok=True)
        for variant_id in info['variants'].keys():
            (duck_dir / variant_id).mkdir(exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(main)
    
    # Create duck blueprints
    open_duck_mini = DuckBlueprint('open_duck_mini', __name__, url_prefix='/open_duck_mini')
    bdx = DuckBlueprint('bdx', __name__, url_prefix='/bdx')
    
    # Register duck blueprints
    app.register_blueprint(open_duck_mini)
    app.register_blueprint(bdx)
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )
    
    # Initialize API routes
    DuckRoutes(app)
    
    return app 
