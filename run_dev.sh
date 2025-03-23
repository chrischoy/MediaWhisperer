#!/bin/bash

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start API server
echo "Starting API server..."

# Check if virtual environment exists, if not create one
if [ -d "$SCRIPT_DIR/.venv" ]; then
    # Activate project-level virtual environment
    echo "Using project-level virtual environment..."
    source "$SCRIPT_DIR/.venv/bin/activate"
elif [ -d "$SCRIPT_DIR/apps/api/venv" ]; then
    # Activate API-level virtual environment
    echo "Using API-level virtual environment..."
    source "$SCRIPT_DIR/apps/api/venv/bin/activate"
else
    echo "No virtual environment found. Please run ./install_deps.sh first."
    exit 1
fi

# Create upload directories
mkdir -p "$SCRIPT_DIR/apps/api/uploads/temp/pdf"

# Start the API server
cd "$SCRIPT_DIR/apps/api"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

# Start frontend server
echo "Starting frontend server..."
cd "$SCRIPT_DIR/apps/frontend"

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start the frontend server
npm run dev &
FRONTEND_PID=$!

# Function to handle exit
function cleanup {
  echo "Stopping servers..."
  kill $API_PID
  kill $FRONTEND_PID
  exit
}

# Trap SIGINT
trap cleanup SIGINT

echo "==================================="
echo "Development servers are running:"
echo "- API: http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo "- Frontend: http://localhost:3000"
echo "==================================="
echo "Press Ctrl+C to stop both servers"

# Wait for user to press Ctrl+C
wait
