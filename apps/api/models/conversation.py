from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MessageRole(str, Enum):
    """Message role enum."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageCreate(BaseModel):
    """Message creation model."""

    content: str
    role: MessageRole = MessageRole.USER


class Message(BaseModel):
    """Message model."""

    id: int
    conversation_id: int
    content: str
    role: MessageRole
    created_at: datetime

    class Config:
        orm_mode = True


class ConversationCreate(BaseModel):
    """Conversation creation model."""

    title: Optional[str] = None


class Conversation(BaseModel):
    """Conversation model."""

    id: int
    pdf_id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: Optional[List[Message]] = None

    class Config:
        orm_mode = True


class ConversationResponse(BaseModel):
    """Conversation response model."""

    id: int
    pdf_id: int
    title: str
    created_at: datetime
    message_count: int

    class Config:
        orm_mode = True
