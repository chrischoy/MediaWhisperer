#!/bin/bash

# Get the absolute path to the script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_SOURCE="$SCRIPT_DIR/.env" # Source env file
API_ENV_TARGET="$SCRIPT_DIR/apps/api/.env"
FRONTEND_ENV_TARGET="$SCRIPT_DIR/apps/frontend/.env"

# Check if root .env exists
if [ ! -f "$ENV_SOURCE" ]; then
    echo "Error: Root .env file ($ENV_SOURCE) not found."
    echo "Please copy .env.example to .env and fill in your values."
    exit 1
fi

echo "Parsing root .env file for API and Frontend variables..."

# --- API Environment Variables ---
# Define API variables (add any new ones here)
API_VARS=(
    SECRET_KEY
    ACCESS_TOKEN_EXPIRE_MINUTES
    DATABASE_URL
    UPLOAD_DIR
    DEV_MODE
    DEV_USER_ID
    ANTHROPIC_API_KEY
    GOOGLE_API_KEY
    PERPLEXITY_API_KEY
    MODEL
    PERPLEXITY_MODEL
    MAX_TOKENS
    TEMPERATURE
    DEBUG
    LOG_LEVEL
    DEFAULT_SUBTASKS
    DEFAULT_PRIORITY
    PROJECT_NAME
)

# Create/clear the target API .env file
> "$API_ENV_TARGET"

# Extract API variables from source .env
for VAR_NAME in "${API_VARS[@]}"; do
    grep "^${VAR_NAME}=" "$ENV_SOURCE" >> "$API_ENV_TARGET"
done
echo "Created $API_ENV_TARGET"

# --- Frontend Environment Variables ---
# Define Frontend variables (add any new ones here)
FRONTEND_VARS=(
    NEXTAUTH_SECRET
    NEXT_PUBLIC_API_URL
    NEXTAUTH_URL
)

# Create/clear the target Frontend .env file
> "$FRONTEND_ENV_TARGET"

# Extract Frontend variables from source .env
for VAR_NAME in "${FRONTEND_VARS[@]}"; do
    grep "^${VAR_NAME}=" "$ENV_SOURCE" >> "$FRONTEND_ENV_TARGET"
done
echo "Created $FRONTEND_ENV_TARGET"

# Start API server
echo "Starting API server..."

# Check if virtual environment exists, if not create one
if [ -d "$SCRIPT_DIR/.venv" ]; then
    # Activate project-level virtual environment
    echo "Using project-level virtual environment..."
    source "$SCRIPT_DIR/.venv/bin/activate"
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
