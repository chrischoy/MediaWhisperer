# MediaWhisperer

## Goals

- Conversation about a PDF file
  - Converts a PDF file into a text + images (tables, figures, etc.)
    - Cleanup footers, headers, page numbers, etc.
  - Summarizes the content
  - Have a conversation with the PDF
- Conversation about a Youtube video
  - Converts a Youtube video into a text + images (frames, etc.)
  - Summarizes the content
  - Have a conversation with the Youtube video
- Hosting it on a personal web server
  - Simple authentication

## Technologies

### Backend

- Python
- Hugging Face
- Google Generative AI (PDF OCR)
- PyTorch
- FastAPI (for API and WebSocket support)

### Frontend

- Next.js (React framework)
- Chakra UI (component library)
- xterm.js (terminal emulation)
- React-PDF (PDF rendering)
- React Player (video embedding)

## Project Structure

```
mediawhisperer/
├── apps/                      # Application components
│   ├── frontend/              # Next.js frontend application
│   ├── api/                   # FastAPI main API service
│   └── workers/               # Background processing workers (future)
│
├── core/                      # Shared core functionality
│   ├── models/                # Data models shared across services
│   ├── config/                # Configuration management
│   ├── utils/                 # Utility functions
│   └── database/              # Database connection and models
│
├── processors/                # Media processing modules
│   ├── pdf/                   # PDF processing logic
│   └── video/                 # Video processing logic
│
├── llm/                       # LLM integration components
│   ├── tools/                 # Custom tools for LLM function calling
│   ├── agents/                # Agent definitions and behaviors
│   ├── prompts/               # Reusable prompt templates
│   └── models/                # Model wrappers and configurations
│
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
├── tests/                     # Test suite
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   └── e2e/                   # End-to-end tests
│
├── .gitignore
├── README.md
├── PROJECT_PLANS.md
└── docker-compose.yml         # For development/production setup
```

## Implementation Plan

### Phase 1: Authentication & Basic Setup

- Set up Next.js project with TypeScript
- Implement authentication with NextAuth.js
  - Email/password authentication
  - Session management
  - Protected routes
- Create basic layout with Chakra UI
  - Responsive design
  - Dark/light mode support
  - Navigation

### Phase 2: Core Functionality

- Implement PDF processing backend
- Create YouTube video processing
- Build conversation interface
- Integrate xterm.js terminal

### Phase 3: Deployment

- Set up production environment
- Configure secure authentication
- Performance optimization
