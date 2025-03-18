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

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Install JavaScript dependencies
echo "📥 Installing JavaScript dependencies..."
npm install

# Generate 3D models
echo "📥 Generating 3D models..."
npm run generate-models

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p generated_motions
mkdir -p submodules/open_duck_playground/open_duck_mini_v2/data
mkdir -p trained_models/bdx
mkdir -p trained_models/open_duck_mini_v2
mkdir -p static/models
mkdir -p static/images
echo ""
echo "---------------------------------------------------------------"
echo ""
echo "✅ Setup complete! You can now:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the web interface: python app.py"
echo "3. Open your browser and navigate to: http://localhost:5000"
echo ""
echo "---------------------------------------------------------------"
echo ""

# Check for CUDA support
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected. CUDA support is available."
    CUDA_AVAILABLE=true
else
    echo "ℹ️ No NVIDIA GPU detected. CUDA support and AWD are not available."
    CUDA_AVAILABLE=false
fi

if [ "$CUDA_AVAILABLE" = false ]; then
    echo "❌ CUDA support is not available. AWD has not been installed."
    echo ""
    echo "---------------------------------------------------------------"
fi
echo "ℹ️ Note: If you encounter any PyTorch-related issues, please visit:"
echo "https://pytorch.org/get-started/locally/"
echo "to get the appropriate installation command for your system." 
