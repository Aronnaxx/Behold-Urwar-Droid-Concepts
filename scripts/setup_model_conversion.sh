#!/bin/bash

# Install Blender
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    brew install blender
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    sudo apt-get update
    sudo apt-get install -y blender
else
    echo "Unsupported operating system"
    exit 1
fi

# Create required directories
mkdir -p static/models

echo "Model conversion dependencies installed successfully!" 
