# Behold-Urwar-Droid-Concepts

A web interface for training and testing duck droid models using reinforcement learning.

## Features

- Generate reference motions using Placo
- Train policies using imitation learning
- Test trained models in a playground environment
- Export models to ONNX format
- Visualize results in 3D

## Prerequisites

- Python 3.8 or higher
- Git
- CUDA-capable GPU (recommended for training)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Behold-Urwar-Droid-Concepts.git
cd Behold-Urwar-Droid-Concepts
```

2. Run the setup script:
```bash
chmod +x setup.sh
./setup.sh
```

3. Activate the virtual environment:
```bash
source .venv/bin/activate
```

4. Start the web interface:
```bash
uv run app.py
```

5. Open your browser and navigate to:
```
http://localhost:5000
```

## Project Structure

```
.
├── app/                    # Core application code
│   ├── routes/            # Flask routes
│   ├── services/          # Business logic
│   ├── static/           # Static assets
│   └── templates/        # HTML templates
├── docs/                  # Documentation
├── generated_motions/     # Storage for generated motions
├── static/               # Global static assets
├── submodules/           # Git submodules
│   ├── open_duck_mini/   # Duck model definitions
│   ├── open_duck_playground/  # Training environment
│   └── open_duck_reference_motion_generator/  # Motion generation
├── templates/            # Global templates
├── trained_models/       # Storage for trained models
├── .env                  # Environment configuration
├── app.py               # Main Flask application
├── pyproject.toml       # Python package configuration
└── setup.sh            # Setup automation script
```

## Development

### Installing Development Dependencies

```bash
uv pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting

Run the formatters:
```bash
black .
isort .
```

## License

MIT License - see LICENSE file for details
