# MediaWhisperer

An interactive tool for processing and conversing with media content including PDF documents and YouTube videos. MediaWhisperer extracts content, summarizes it, and allows you to have natural language conversations about the media.

## Features

- **PDF Processing**

  - Extract text and images from PDF files
  - Clean up headers, footers, page numbers, etc.
  - Summarize content using LLM models
  - Have interactive conversations about the PDF content

- **YouTube Video Processing**

  - Convert YouTube videos into text transcripts and key frames
  - Summarize video content
  - Have interactive conversations about the video content

- **User-Friendly Interface**

  - Web-based interface built with Next.js
  - Terminal-like experience using xterm.js
  - PDF rendering and video embedding
  - Dark/light mode support

- **Secure Deployment**
  - Host on personal web server
  - Simple authentication system

## Getting Started

See [SETUP.md](SETUP.md) for detailed setup instructions.

### Quick Start

#### Using uv (recommended)

```bash
# Install the project in development mode
uv venv apps/api/venv
source apps/api/venv/bin/activate
uv pip install -e .

# Setup the frontend
cd apps/frontend
npm install

# Run both servers
cd ..
./run_dev.sh
```

#### Using pip

```bash
# Setup the backend
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r ../../requirements.txt
mkdir -p uploads/temp/pdf

# Setup the frontend
cd ../frontend
npm install

# Run both servers
cd ../..
./run_dev.sh
```

## Project Structure

- **apps/frontend** - Next.js frontend application
- **apps/api** - FastAPI backend API
- **core** - Shared core functionality
- **processors** - Media processing modules
- **llm** - LLM integration components

## Next Steps

See [NEXT_STEPS.md](NEXT_STEPS.md) for planned development tasks.

## License

This project is open-source and available for personal and research use.
