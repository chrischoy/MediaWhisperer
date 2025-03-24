from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database.models import Conversation, Message
from ..models.conversation import ConversationCreate, ConversationUpdate, MessageCreate, MessageRole
from .base import BaseRepository


class ConversationRepository(BaseRepository[Conversation, ConversationCreate, ConversationUpdate]):
    """Repository for conversation operations."""

    def __init__(self):
        super().__init__(Conversation)

    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all conversations for a specific user."""
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_pdf(self, db: Session, pdf_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all conversations for a specific PDF document."""
        return (
            db.query(Conversation)
            .filter(Conversation.pdf_id == pdf_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_user_and_pdf(
        self, db: Session, user_id: int, pdf_id: int, skip: int = 0, limit: int = 100
    ) -> List[Conversation]:
        """Get all conversations for a specific user and PDF document."""
        return (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id, Conversation.pdf_id == pdf_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def add_message(self, db: Session, conversation_id: int, content: str, role: MessageRole) -> Message:
        """Add a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            role=role,
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    def get_messages(self, db: Session, conversation_id: int) -> List[Message]:
        """Get all messages for a conversation ordered by creation time."""
        return (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )


# Create a singleton instance
conversation_repository = ConversationRepository()