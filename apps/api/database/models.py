import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Mock Database Models for demonstration


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pdfs = relationship("PDFDocument", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class PDFDocument(Base):
    """PDF document model."""

    __tablename__ = "pdf_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(Text, nullable=True)
    filename = Column(String)
    file_path = Column(String)
    extracted_text = Column(Text, nullable=True)
    status = Column(String, default="pending")
    page_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="pdfs")
    pages = relationship("PDFPage", back_populates="pdf", cascade="all, delete-orphan")
    conversations = relationship(
        "Conversation", back_populates="pdf", cascade="all, delete-orphan"
    )


class PDFPage(Base):
    """PDF page model."""

    __tablename__ = "pdf_pages"

    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id"))
    page_number = Column(Integer)
    text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    pdf = relationship("PDFDocument", back_populates="pages")
    images = relationship(
        "PDFImage", back_populates="page", cascade="all, delete-orphan"
    )


class PDFImage(Base):
    """PDF image model."""

    __tablename__ = "pdf_images"

    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pdf_pages.id"))
    image_path = Column(String)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    page = relationship("PDFPage", back_populates="images")


class Conversation(Base):
    """Conversation model."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_documents.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pdf = relationship("PDFDocument", back_populates="conversations")
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class MessageRoleEnum(str, enum.Enum):
    """Message role enum."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base):
    """Message model."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    content = Column(Text)
    role = Column(Enum(MessageRoleEnum), default=MessageRoleEnum.USER)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


# Alias for backward compatibility with existing code
PDF = PDFDocument
