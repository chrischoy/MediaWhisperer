# MediaWhisperer Setup Guide

This guide will help you set up the MediaWhisperer project for development.

## Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

## Backend Setup (FastAPI)

### Option 1: Using uv (recommended)

1. Install the project in development mode:

```bash
# From the project root
uv venv apps/api/venv
source apps/api/venv/bin/activate
uv pip install -e .
```

### Option 2: Using pip

1. Navigate to the API directory:

```bash
cd apps/api
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate the virtual environment:

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r ../../requirements.txt
```

5. Create necessary directories:

```bash
mkdir -p uploads/temp/pdf
```

6. Start the API server:

```bash
python main.py
```

The API will be available at http://localhost:8000, and API documentation at http://localhost:8000/docs.

## Frontend Setup (Next.js)

1. Navigate to the frontend directory:

```bash
cd apps/frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm run dev
```

The frontend will be available at http://localhost:3000.

## Running Both Servers

For convenience, you can use the provided script to run both servers simultaneously:

```bash
./run_dev.sh
```

This script will:

1. Start the API server
2. Start the frontend development server
3. Display URLs for accessing both services

You can press Ctrl+C to stop both servers.

## Default Login Credentials

Use these credentials to log in to the application:

- Email: admin@example.com
- Password: password

## Configuration

- Backend: Configuration is managed in `apps/api/.env`
- Frontend: Configuration is managed in `apps/frontend/.env.local`
