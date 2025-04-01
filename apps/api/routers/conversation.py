from typing import List, Optional

from database.session import get_db
from dependencies import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from models.conversation import (
    Conversation,
    ConversationCreate,
    ConversationResponse,
    ConversationWithMessages,
    Message,
    MessageCreate,
    MessageRole,
)
from models.user import User
from repositories.conversation import conversation_repository
from repositories.pdf import pdf_repository
from services.conversation_service import generate_assistant_response
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("", response_model=Conversation, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_in: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new conversation for a PDF."""
    # Verify PDF exists and user has access
    pdf = pdf_repository.get(db, conversation_in.pdf_id)
    if not pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found",
        )

    if pdf.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this PDF",
        )

    # Create title if not provided
    if not conversation_in.title:
        conversation_in.title = f"Conversation about {pdf.title}"

    # Create conversation
    conversation_data = conversation_in.model_dump()
    conversation_data["user_id"] = current_user.id
    conversation = conversation_repository.create(db, conversation_data)

    # Add system message to start the conversation
    system_message = "I'm an AI assistant that can help you understand the content of this PDF document. What would you like to know about it?"
    conversation_repository.add_message(
        db, conversation.id, system_message, MessageRole.SYSTEM
    )

    return conversation


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    pdf_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List conversations for the current user, optionally filtered by PDF."""
    if pdf_id:
        conversations = conversation_repository.get_by_user_and_pdf(
            db, current_user.id, pdf_id, skip, limit
        )
    else:
        conversations = conversation_repository.get_by_user(
            db, current_user.id, skip, limit
        )

    # Add message counts to each conversation
    result = []
    for conv in conversations:
        messages = conversation_repository.get_messages(db, conv.id)
        result.append({**conv.__dict__, "message_count": len(messages)})

    return result


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a conversation with all messages."""
    conversation = conversation_repository.get(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation",
        )

    messages = conversation_repository.get_messages(db, conversation_id)

    return {**conversation.__dict__, "messages": messages}


@router.post("/{conversation_id}/messages", response_model=Message)
async def add_message(
    conversation_id: int,
    message: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a message to a conversation and generate an AI response."""
    conversation = conversation_repository.get(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this conversation",
        )

    # Add the user message
    user_message = conversation_repository.add_message(
        db, conversation_id, message.content, MessageRole.USER
    )

    # Get the PDF document to provide context
    pdf = pdf_repository.get(db, conversation.pdf_id)
    if not pdf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF not found",
        )

    # Get previous messages for context
    messages = conversation_repository.get_messages(db, conversation_id)

    # Generate AI response
    context = pdf.extracted_text or ""
    response_content = await generate_assistant_response(
        context, messages, message.content
    )

    # Add the AI response to the conversation
    conversation_repository.add_message(
        db, conversation_id, response_content, MessageRole.ASSISTANT
    )

    return user_message


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a conversation."""
    conversation = conversation_repository.get(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this conversation",
        )

    success = conversation_repository.delete(db, conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation",
        )

    return None
