from pathlib import Path
import os
import importlib.util

# Re-export the DuckConfig class and instance
from .duck_config import DuckConfig, duck_config

# Base paths and default configurations
ROOT_DIR = Path(__file__).parent.parent.parent
OUTPUT_DIR = ROOT_DIR / 'output'
TRAINED_MODELS_DIR = OUTPUT_DIR / 'trained_models'
GENERATED_MOTIONS_DIR = OUTPUT_DIR / 'generated_motions'

# Create directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_MOTIONS_DIR.mkdir(parents=True, exist_ok=True)

# Directory Paths
PLAYGROUND_DIR = Path('submodules/open_duck_playground')
REFERENCE_MOTION_DIR = lambda duck_type: Path(f'submodules/open_duck_playground/{duck_type}/data')
AWD_DIR = Path('submodules/awd')
STATIC_DIR = Path('static')

# Custom Logo Configuration
# Set to None to use default robot icon, or set to path relative to static directory
# Example: 'images/logo.png'
CUSTOM_LOGO_PATH = None

# Learning content structure
LEARNING_CONTENT = {
    'gait': {
        'title': 'Gait Generation',
        'model_path': '/static/models/gait.glb',
        'overview': 'Understanding how ducks walk and generating natural gaits.',
        'how_it_works': [
            'Analysis of duck walking patterns',
            'Mathematical modeling of joint movements',
            'Dynamic balance considerations'
        ],
        'examples': [
            {'title': 'Basic Walk', 'description': 'Simple forward walking motion'},
            {'title': 'Turn', 'description': 'Turning while maintaining balance'},
            {'title': 'Variable Speed', 'description': 'Adjusting walking speed dynamically'}
        ],
        'key_concepts': [
            'Center of Mass',
            'Zero Moment Point',
            'Joint Trajectories'
        ],
        'resources': [
            {'title': 'Duck Locomotion Paper', 'url': '#'},
            {'title': 'Gait Analysis Video', 'url': '#'}
        ]
    },
    'training': {
        'title': 'Model Training',
        'model_path': '/static/models/training.glb',
        'overview': 'Training models for natural duck movement.',
        'how_it_works': [
            'Reference motion collection',
            'Reinforcement learning approach',
            'Policy optimization'
        ],
        'examples': [
            {'title': 'Basic Training', 'description': 'Training a simple walking policy'},
            {'title': 'Advanced Training', 'description': 'Training with multiple objectives'}
        ],
        'key_concepts': [
            'Policy Networks',
            'Reward Functions',
            'Training Environments'
        ],
        'resources': [
            {'title': 'RL in Robotics', 'url': '#'},
            {'title': 'Training Guide', 'url': '#'}
        ]
    }
}

class Config:
    """Base configuration."""
    SECRET_KEY = 'dev'  # Change this in production
    FLASK_APP = 'app.py'
    FLASK_ENV = 'development'
    PORT = 5003  # Set the port to 5003
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = str(ROOT_DIR / 'uploads')
    ALLOWED_EXTENSIONS = {'json', 'pkl', 'onnx'}
    
    # Training settings
    DEFAULT_NUM_ENVS = 4096
    MAX_NUM_ENVS = 8192
    MIN_NUM_ENVS = 1
    
    # Device settings
    DEFAULT_SERIAL_BAUDRATE = 115200
    DEFAULT_SSH_PORT = 22
    
    # Paths
    ROOT_DIR = str(ROOT_DIR)
    OUTPUT_DIR = str(OUTPUT_DIR)
    TRAINED_MODELS_DIR = str(TRAINED_MODELS_DIR)
    GENERATED_MOTIONS_DIR = str(GENERATED_MOTIONS_DIR)

class ProductionConfig(Config):
    """Production configuration."""
    FLASK_ENV = 'production'
    # Add production-specific settings here

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Add development-specific settings here

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    # Add testing-specific settings here 