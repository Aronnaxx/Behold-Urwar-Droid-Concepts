from pathlib import Path
from datetime import datetime

# Duck Types Configuration
DUCK_TYPES = {
    'bdx': 'BDX Duck',
    'open_duck_mini_v2': 'Open Duck Mini V2'
}

# Directory Paths
OUTPUT_DIR = Path('generated_motions')
PLAYGROUND_DIR = Path('submodules/open_duck_playground')
REFERENCE_MOTION_DIR = lambda duck_type: Path(f'submodules/open_duck_playground/{duck_type}/data')
AWD_DIR = Path('submodules/awd')
TRAINED_MODELS_DIR = Path('trained_models')
STATIC_DIR = Path('static')

# Custom Logo Configuration
# Set to None to use default robot icon, or set to path relative to static directory
# Example: 'images/logo.png'
CUSTOM_LOGO_PATH = None

# Learning Center Content
LEARNING_CONTENT = {
    'motion_generation': {
        'title': 'Motion Generation',
        'model_path': '/static/models/motion_generation.glb',
        'overview': '''
            <p>Motion generation is the first step in training a Duck Droid. This process creates a diverse set of reference motions
            that serve as the foundation for learning complex behaviors.</p>
            <p>Our motion generation system uses advanced algorithms to create natural, physically plausible movements
            that the droid can learn to imitate and improve upon.</p>
        ''',
        'how_it_works': '''
            <p>The motion generation process involves several key steps:</p>
            <ol>
                <li>Define motion parameters and constraints</li>
                <li>Generate initial motion trajectories</li>
                <li>Optimize for physical feasibility</li>
                <li>Validate against real-world constraints</li>
            </ol>
        ''',
        'examples': '''
            <p>Here are some example motions that can be generated:</p>
            <ul>
                <li>Walking gaits</li>
                <li>Turning maneuvers</li>
                <li>Balance recovery</li>
                <li>Obstacle navigation</li>
            </ul>
        ''',
        'key_concepts': [
            'Motion planning and optimization',
            'Physical constraints and feasibility',
            'Natural movement patterns',
            'Trajectory generation'
        ],
        'resources': [
            {
                'title': 'Motion Planning Documentation',
                'description': 'Detailed guide to motion planning algorithms',
                'url': '#'
            },
            {
                'title': 'Example Motions',
                'description': 'Collection of pre-generated motion examples',
                'url': '#'
            }
        ]
    },
    'training': {
        'title': 'Training Process',
        'model_path': '/static/models/training.glb',
        'overview': '''
            <p>The training process uses reinforcement learning to teach the Duck Droid complex behaviors.
            This phase builds upon the reference motions generated earlier to create a robust control policy.</p>
        ''',
        'how_it_works': '''
            <p>Training involves:</p>
            <ol>
                <li>Setting up the training environment</li>
                <li>Defining reward functions</li>
                <li>Running parallel training episodes</li>
                <li>Optimizing the policy network</li>
            </ol>
        ''',
        'examples': '''
            <p>Training scenarios include:</p>
            <ul>
                <li>Learning to walk on various terrains</li>
                <li>Adapting to different payloads</li>
                <li>Recovering from disturbances</li>
                <li>Following complex paths</li>
            </ul>
        ''',
        'key_concepts': [
            'Reinforcement learning',
            'Policy optimization',
            'Reward shaping',
            'Environment simulation'
        ],
        'resources': [
            {
                'title': 'Training Guide',
                'description': 'Comprehensive guide to the training process',
                'url': '#'
            }
        ]
    },
    'playground': {
        'title': 'Mujoco Playground',
        'model_path': '/static/models/playground.glb',
        'overview': '''
            <p>The Mujoco Playground provides a realistic simulation environment for testing and visualizing
            trained models. It allows you to interact with the droid and observe its behavior in real-time.</p>
        ''',
        'how_it_works': '''
            <p>The playground features:</p>
            <ul>
                <li>Real-time physics simulation</li>
                <li>Interactive controls</li>
                <li>Performance metrics</li>
                <li>Visual debugging tools</li>
            </ul>
        ''',
        'examples': '''
            <p>You can use the playground to:</p>
            <ul>
                <li>Test trained models</li>
                <li>Analyze performance</li>
                <li>Debug behaviors</li>
                <li>Record demonstrations</li>
            </ul>
        ''',
        'key_concepts': [
            'Physics simulation',
            'Real-time visualization',
            'Performance analysis',
            'Interactive testing'
        ],
        'resources': [
            {
                'title': 'Playground Guide',
                'description': 'Guide to using the Mujoco Playground',
                'url': '#'
            }
        ]
    }
} 
