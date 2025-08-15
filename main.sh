#!/bin/bash

# Script functions:
# 1. Check if venv exists, create if not
# 2. Check if requirements.txt dependencies are satisfied in venv, install/update if not
# 3. Launch main.py

set -e  # Exit on error

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "Project directory: $PROJECT_DIR"

# Check if we are in a virtual environment
if [[ "$VIRTUAL_ENV" == "" ]]; then
    VENV_PATH="$PROJECT_DIR/.venv"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_PATH" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_PATH"
    else
        echo "Found existing virtual environment"
    fi
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
else
    echo "Already in virtual environment: $VIRTUAL_ENV"
fi

# Upgrade pip to the latest version
echo "Upgrading pip..."
pip install --upgrade pip

# Check and install dependencies
echo "Checking and installing project dependencies..."
pip install -r "$PROJECT_DIR/requirements.txt"

# Launch application
echo "Launching application..."
python "$PROJECT_DIR/main.py"