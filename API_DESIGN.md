# MediaWhisperer API Design (Phase 1)

## Overview

The MediaWhisperer API service built with FastAPI focuses initially on user management and PDF processing functionality.

## File Structure

```
apps/api/
├── main.py                      # FastAPI application entry point
├── config.py                    # Configuration settings
├── dependencies.py              # Dependency injection
│
├── routers/                     # API endpoints
│   ├── __init__.py
│   ├── auth.py                  # User authentication endpoints
│   └── pdf.py                   # PDF processing endpoints
│
├── services/                    # Business logic
│   ├── __init__.py
│   ├── auth_service.py          # Authentication service
│   ├── pdf_service.py           # PDF processing service
│   └── conversation_service.py  # PDF conversation service
│
├── models/                      # Data models
│   ├── __init__.py
│   ├── user.py                  # User models
│   ├── pdf.py                   # PDF models
│   └── conversation.py          # Conversation models
│
└── utils/                       # Utility functions
    ├── __init__.py
    ├── security.py              # Password hashing, JWT
    └── storage.py               # File storage functions
```

## Class Hierarchy

### PDF Processing

```
PDFProcessor
├── PDFTextExtractor         # Extracts raw text from PDF
├── PDFImageExtractor        # Extracts images from PDF
├── PDFCleanupProcessor      # Removes headers, footers, page numbers
└── PDFStructureAnalyzer     # Identifies sections, paragraphs
```

### Conversation Management

```
ConversationManager
├── ContextBuilder           # Builds context from PDF content
└── MessageHandler           # Handles user-PDF conversation
```

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login (returns JWT)
- `GET /api/auth/me` - Get current user profile

### PDF Processing

- `POST /api/pdf/upload` - Upload PDF file
- `GET /api/pdf/list` - List user's PDFs
- `GET /api/pdf/{pdf_id}` - Get PDF details
- `GET /api/pdf/{pdf_id}/content` - Get processed PDF content
- `GET /api/pdf/{pdf_id}/summary` - Get PDF summary

### Conversation

- `POST /api/pdf/{pdf_id}/conversation` - Start new conversation
- `GET /api/pdf/{pdf_id}/conversation/{conv_id}` - Get conversation
- `POST /api/pdf/{pdf_id}/conversation/{conv_id}/message` - Send message
- `GET /api/pdf/{pdf_id}/conversation/{conv_id}/messages` - Get messages

## Data Models

### User Model

```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class User(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime
```

### PDF Models

```python
class PDFCreate(BaseModel):
    title: str
    description: Optional[str] = None

class PDFDocument(BaseModel):
    id: int
    title: str
    description: Optional[str]
    file_path: str
    user_id: int
    status: str  # processing, ready, error
    page_count: Optional[int]
    created_at: datetime
    updated_at: datetime
```

### Conversation Models

```python
class MessageCreate(BaseModel):
    content: str

class Message(BaseModel):
    id: int
    conversation_id: int
    content: str
    role: str  # user or assistant
    created_at: datetime

class Conversation(BaseModel):
    id: int
    pdf_id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
```

## PDF Processing Pipeline

1. **Upload**

   - Validate PDF file
   - Store in file system
   - Create database entry with status "processing"

2. **Text Extraction**

   - Extract text using PyPDF2/pymupdf
   - Maintain page boundaries and structure

3. **Cleanup**

   - Remove headers, footers, page numbers
   - Fix hyphenation and line breaks

4. **Image Extraction**

   - Extract embedded images
   - Maintain positioning information

5. **Summarization**

   - Generate summary using LLM
   - Identify key topics and entities

6. **Indexing**
   - Create vector embeddings for retrieval
   - Store in database for efficient querying
   - Update status to "ready"

## Authentication Flow

1. User registers with email/password
2. Password is hashed and stored
3. User logs in and receives JWT token
4. API requests include JWT in Authorization header
5. Protected routes validate JWT and identify user
