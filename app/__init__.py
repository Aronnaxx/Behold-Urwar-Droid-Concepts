from flask import Flask
from flask_cors import CORS
from pathlib import Path
from datetime import datetime
from .config import Config, OUTPUT_DIR, TRAINED_MODELS_DIR, GENERATED_MOTIONS_DIR
from .routes.main import main
from .routes.duck import DuckBlueprint
from .routes.routes import DuckRoutes
import logging

def create_app(config_class=Config):
    """Create and configure the Flask application."""
    # Get the root directory (where templates are located)
    root_dir = Path(__file__).parent.parent
    app = Flask(__name__, 
                template_folder=str(root_dir / 'app/templates'),
                static_folder=str(root_dir / 'app/static'))
    
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
    GENERATED_MOTIONS_DIR.mkdir(exist_ok=True)

    # Create duck type directories from configuration
    from .config import duck_config
    for duck_type_config in duck_config.list_duck_types():
        duck_type = duck_type_config['id']
        duck_dir = TRAINED_MODELS_DIR / duck_type
        duck_dir.mkdir(exist_ok=True)
        
        # Get variants for this duck type and create directories for each
        duck_config_obj = duck_config.get_duck_type(duck_type)
        if duck_config_obj and 'variants' in duck_config_obj:
            for variant_id in duck_config_obj['variants'].keys():
                (duck_dir / variant_id).mkdir(exist_ok=True)
    
    # Create duck type directories from configuration
    from .config import duck_config
    for duck_type_config in duck_config.list_duck_types():
        duck_type = duck_type_config['id']
        duck_dir = GENERATED_MOTIONS_DIR / duck_type
        duck_dir.mkdir(exist_ok=True)
        
        # Get variants for this duck type and create directories for each
        duck_config_obj = duck_config.get_duck_type(duck_type)
        if duck_config_obj and 'variants' in duck_config_obj:
            for variant_id in duck_config_obj['variants'].keys():
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
