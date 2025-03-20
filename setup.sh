#!/bin/bash

# Exit on error
set -e

echo "Setting up Behold-Urwar-Droid-Concepts..."

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create and activate virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install uv in the virtual environment
echo "Installing uv in virtual environment..."
pip install uv

# Initialize and update submodules
echo "Initializing submodules..."
git submodule update --init --recursive

# Install the package in development mode
echo "Installing package in development mode..."
uv pip install -e ".[dev]"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p app/static app/templates docs generated_motions trained_models

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOL
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Training Configuration
TRAINING_EPOCHS=10
LEARNING_RATE=0.001
BATCH_SIZE=32

# Output Directories
OUTPUT_DIR=generated_motions
TRAINED_MODELS_DIR=trained_models
EOL
fi

# Set proper permissions
chmod +x setup.sh

echo "Setup complete! Don't forget to:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Configure your .env file if needed"
echo "3. Run the application: python app.py" 
