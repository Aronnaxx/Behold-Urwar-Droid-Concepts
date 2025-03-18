#!/bin/bash

# Exit on error
set -e

echo "🚀 Setting up Behold Urwar Droid Concepts..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Create and activate virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install common dependencies
echo "📥 Installing common dependencies..."
pip install --upgrade pip
pip install wheel setuptools

# Function to install requirements from a submodule
install_submodule_requirements() {
    local submodule=$1
    local requirements_file=$2
    
    if [ -f "$submodule/$requirements_file" ]; then
        echo "📥 Installing requirements for $submodule..."
        pip install -r "$submodule/$requirements_file"
    else
        echo "⚠️ No requirements file found for $submodule at $requirements_file"
    fi
}

# Install requirements for each submodule
install_submodule_requirements "submodules/open_duck_mini" "requirements.txt"
install_submodule_requirements "submodules/awd" "requirements.txt"
install_submodule_requirements "submodules/open_duck_playground" "requirements.txt"
install_submodule_requirements "submodules/open_duck_reference_motion_generator" "requirements.txt"

# Check for uv (optional but recommended)
if ! command -v uv &> /dev/null; then
    echo "ℹ️ uv is not installed. Installing uv (recommended for some submodules)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

echo "✅ Setup complete! You can now:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Launch the playground: cd submodules/open_duck_playground && python launch_playground.py" 
