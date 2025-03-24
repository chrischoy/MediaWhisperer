from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from .session import Base


class User(Base):
    """User model for authentication and user management."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    pdf_documents = relationship("PDFDocument", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")


class PDFDocument(Base):
    """PDF document model for storing metadata about uploaded PDFs."""

    __tablename__ = "pdf_documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False, unique=True)
    status = Column(String(50), nullable=False)  # pending, processing, completed, failed
    page_count = Column(Integer)
    extracted_text = Column(Text)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="pdf_documents")
    pages = relationship("PDFPage", back_populates="pdf_document", cascade="all, delete-orphan")
    images = relationship("PDFImage", back_populates="pdf_document", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="pdf_document", cascade="all, delete-orphan")
    embeddings = relationship("PDFEmbedding", back_populates="pdf_document", cascade="all, delete-orphan")


class PDFPage(Base):
    """PDF page model for storing text content of individual pages."""

    __tablename__ = "pdf_pages"

    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Uniqueness constraint
    __table_args__ = (UniqueConstraint("pdf_id", "page_number", name="unique_pdf_page"),)

    # Relationships
    pdf_document = relationship("PDFDocument", back_populates="pages")


class PDFImage(Base):
    """PDF image model for storing extracted images from PDF files."""

    __tablename__ = "pdf_images"

    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer, nullable=False)
    image_path = Column(String(255), nullable=False, unique=True)
    width = Column(Integer)
    height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    pdf_document = relationship("PDFDocument", back_populates="images")


class Conversation(Base):
    """Conversation model for storing chat sessions about PDFs."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="conversations")
    pdf_document = relationship("PDFDocument", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for storing conversation messages."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class PDFEmbedding(Base):
    """PDF embedding model for vector search capabilities."""

    __tablename__ = "pdf_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id", ondelete="CASCADE"), nullable=False)
    page_number = Column(Integer)
    chunk_index = Column(Integer, nullable=False)
    text_chunk = Column(Text, nullable=False)
    # embedding = Column(Vector(1536))  # Using OpenAI's embedding dimension
    # This requires pgvector extension, which we'll configure separately
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    pdf_document = relationship("PDFDocument", back_populates="embeddings")