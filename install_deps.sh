#!/bin/bash

# Script to install dependencies with correct versions

cd "$(dirname "$0")"

# Ensure virtual environment exists
if [ ! -d "./.venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv
fi

# Activate virtual environment
source ./.venv/bin/activate

# Install pinned versions of problematic packages
echo "Installing critical dependencies..."
pip uninstall -y bcrypt passlib
pip install bcrypt==3.2.2
pip install passlib[bcrypt]==1.7.4
pip install email-validator

# Install the rest of the project
echo "Installing project..."
uv pip install -e .

echo "Installation complete!"
