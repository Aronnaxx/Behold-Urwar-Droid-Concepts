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
python3 -m venv .venv
source .venv/bin/activate

# Install common dependencies
echo "📥 Installing common dependencies..."
pip install --upgrade pip
pip install wheel setuptools

# Check for CUDA support
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected. CUDA support is available."
    CUDA_AVAILABLE=true
else
    echo "ℹ️ No NVIDIA GPU detected. CUDA support and AWD are not available."
    CUDA_AVAILABLE=false
fi

# Install PyTorch first with appropriate version
echo "📥 Installing PyTorch..."
if [ "$CUDA_AVAILABLE" = true ]; then
    echo "Installing PyTorch with CUDA support..."
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    install_submodule_requirements "submodules/awd/" "requirements.txt"
else
    echo "Installing PyTorch CPU version..."
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install Flask application requirements
echo "📥 Installing Flask application requirements..."
pip install -r requirements.txt

# Check for uv (optional but recommended)
if ! command -v uv &> /dev/null; then
    echo "ℹ️ uv is not installed. Installing uv (recommended for some submodules)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Create necessary directories
echo ""
echo "---------------------------------------------------------------"
echo ""
echo "✅ Setup complete! You can now:"
echo "1. Activate the virtual environment: source .venv/bin/activate"
echo "2. Start the web interface: python app.py"
echo "3. Open your browser and navigate to: http://localhost:5000"
echo ""
echo "---------------------------------------------------------------"
echo ""
if [ "$CUDA_AVAILABLE" = false ]; then
    echo "❌ CUDA support is not available. AWD has not been installed."
    echo ""
    echo "---------------------------------------------------------------"
fi
echo "ℹ️ Note: If you encounter any PyTorch-related issues, please visit:"
echo "https://pytorch.org/get-started/locally/"
echo "to get the appropriate installation command for your system." 
