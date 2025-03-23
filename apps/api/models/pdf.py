from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ProcessingStatus(str, Enum):
    """PDF processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PDFCreate(BaseModel):
    """PDF creation model."""

    title: str
    description: Optional[str] = None


class PDFPage(BaseModel):
    """PDF page model."""

    page_number: int
    text: str
    images: List[str] = []


class PDFSummary(BaseModel):
    """PDF summary model."""

    title: str
    key_points: List[str]
    summary: str


class PDFDocument(BaseModel):
    """PDF document model."""

    id: int
    title: str
    description: Optional[str] = None
    filename: str
    file_path: str
    user_id: int
    status: ProcessingStatus
    page_count: Optional[int] = None
    extracted_text: Optional[str] = None
    pages: Optional[List[PDFPage]] = None
    summary: Optional[PDFSummary] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class PDFResponse(BaseModel):
    """PDF response model."""

    id: int
    title: str
    description: Optional[str] = None
    filename: str
    status: ProcessingStatus
    page_count: Optional[int] = None
    created_at: datetime

    class Config:
        orm_mode = True
