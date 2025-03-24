# MediaWhisperer Database Design

## Overview

This document outlines the database design for the MediaWhisperer application. We'll be using SQLAlchemy with PostgreSQL to manage user data, media files, and conversations.

## Database Schema

### Users

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### PDF Documents

```sql
CREATE TABLE pdf_documents (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- pending, processing, completed, failed
    page_count INTEGER,
    extracted_text TEXT,
    summary TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    CONSTRAINT unique_file_path UNIQUE (file_path)
);
```

### PDF Pages

```sql
CREATE TABLE pdf_pages (
    id SERIAL PRIMARY KEY,
    pdf_id INTEGER NOT NULL REFERENCES pdf_documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    text TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_pdf_page UNIQUE (pdf_id, page_number)
);
```

### PDF Images

```sql
CREATE TABLE pdf_images (
    id SERIAL PRIMARY KEY,
    pdf_id INTEGER NOT NULL REFERENCES pdf_documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_image_path UNIQUE (image_path)
);
```

### Conversations

```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pdf_id INTEGER NOT NULL REFERENCES pdf_documents(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);
```

### Messages

```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,  -- user, assistant, system
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);
```

### Vector Embeddings

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE pdf_embeddings (
    id SERIAL PRIMARY KEY,
    pdf_id INTEGER NOT NULL REFERENCES pdf_documents(id) ON DELETE CASCADE,
    page_number INTEGER,
    chunk_index INTEGER NOT NULL,
    text_chunk TEXT NOT NULL,
    embedding vector(1536) NOT NULL,  -- Using OpenAI's embedding dimension
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX pdf_embeddings_idx ON pdf_embeddings USING ivfflat (embedding vector_cosine_ops);
```

## SQLAlchemy Models

We'll create SQLAlchemy ORM models that map to these database tables for use in our FastAPI application. The models will be defined in the `models` directory with relationships between tables properly established.

## Database Setup

1. Install PostgreSQL and create a new database for MediaWhisperer
2. Configure database connection in the application settings
3. Set up migrations using Alembic
4. Create initial migration to generate the schema

## Implementation Plan

1. Add SQLAlchemy and PostgreSQL dependencies
2. Create database models in `database/models.py`
3. Set up database connection with `database/session.py`
4. Implement Alembic for migrations
5. Update services to use database models instead of mock data
6. Add database utility functions and repositories

## Security Considerations

- Store database credentials securely using environment variables
- Implement connection pooling for efficient database access
- Add proper error handling for database operations
- Ensure proper index creation for query performance