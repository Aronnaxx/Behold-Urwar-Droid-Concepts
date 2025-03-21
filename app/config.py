from pathlib import Path
from datetime import datetime

# Base paths
ROOT_DIR = Path(__file__).parent.parent
OUTPUT_DIR = ROOT_DIR / 'output'
TRAINED_MODELS_DIR = ROOT_DIR / 'trained_models'
GENERATED_MOTIONS_DIR = ROOT_DIR / 'generated_motions'

# Create directories if they don't exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRAINED_MODELS_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_MOTIONS_DIR.mkdir(parents=True, exist_ok=True)

# Duck types and their display names
DUCK_TYPES = {
    'open_duck_mini': {
        'name': 'Open Duck Mini',
        'variants': {
            'v1': {
                'name': 'Version 1',
                'internal_name': 'open_duck_mini_v1',
                'model_path': '/static/models/open_duck_mini_v2.glb',  # Using v2 model as placeholder
                'description': 'The first generation of Open Duck Mini.',
                'specifications': {
                    'weight': 0.8,  # kg
                    'height': 0.25,  # meters
                    'max_speed': 0.5,  # m/s
                    'battery_life': '1 hour',
                    'motor_type': 'Servo X1'
                }
            },
            'v2': {
                'name': 'Version 2',
                'internal_name': 'open_duck_mini_v2',
                'model_path': '/static/models/open_duck_mini_v2.glb',
                'description': 'Second generation with improved stability and control.',
                'specifications': {
                    'weight': 0.9,  # kg
                    'height': 0.25,  # meters
                    'max_speed': 0.7,  # m/s
                    'battery_life': '1.5 hours',
                    'motor_type': 'Servo X2'
                }
            },
            'v3': {
                'name': 'Version 3',
                'internal_name': 'open_duck_mini_v3',
                'model_path': '/static/models/open_duck_mini_v2.glb',  # Using v2 model as placeholder
                'description': 'Latest generation with advanced features.',
                'specifications': {
                    'weight': 1.0,  # kg
                    'height': 0.27,  # meters
                    'max_speed': 0.8,  # m/s
                    'battery_life': '2 hours',
                    'motor_type': 'Servo X3'
                }
            }
        }
    },
    'bdx': {
        'name': 'BD-X',
        'variants': {
            'go1': {
                'name': 'Go1',
                'internal_name': 'go_bdx',
                'model_path': '/static/models/bdx.glb',
                'description': 'BD-X Go1 variant optimized for agility.',
                'specifications': {
                    'weight': 12.0,  # kg
                    'height': 0.35,  # meters
                    'max_speed': 3.5,  # m/s
                    'battery_life': '2.5 hours',
                    'motor_type': 'Unitree A1',
                    'payload_capacity': '5kg'
                }
            },
            'go2': {
                'name': 'Go2',
                'internal_name': 'go2_bdx',
                'model_path': '/static/models/bdx.glb',
                'description': 'BD-X Go2 with enhanced payload capacity.',
                'specifications': {
                    'weight': 15.0,  # kg
                    'height': 0.40,  # meters
                    'max_speed': 3.0,  # m/s
                    'battery_life': '3 hours',
                    'motor_type': 'Unitree A2',
                    'payload_capacity': '10kg'
                }
            },
            'cybergear': {
                'name': 'Cybergear',
                'internal_name': 'cybergear_bdx',
                'model_path': '/static/models/bdx.glb',
                'description': 'BD-X Cybergear featuring advanced motor control.',
                'specifications': {
                    'weight': 13.5,  # kg
                    'height': 0.38,  # meters
                    'max_speed': 3.2,  # m/s
                    'battery_life': '2.8 hours',
                    'motor_type': 'CyberDyne X1',
                    'payload_capacity': '8kg'
                }
            },
            'servo': {
                'name': 'Servo',
                'internal_name': 'servo_bdx',
                'model_path': '/static/models/bdx.glb',
                'description': 'BD-X Servo with precise movement control.',
                'specifications': {
                    'weight': 11.0,  # kg
                    'height': 0.33,  # meters
                    'max_speed': 2.8,  # m/s
                    'battery_life': '3.2 hours',
                    'motor_type': 'ServoTech Pro',
                    'payload_capacity': '4kg'
                }
            }
        }
    }
}

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