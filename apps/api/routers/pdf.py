import os
from typing import List, Optional

from dependencies import get_current_user
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from models.pdf import PDFCreate, PDFDocument, PDFResponse, ProcessingStatus
from models.user import User
from utils.storage import save_upload_file

from config import settings

router = APIRouter()

# Mock database for demonstration
# In a real app, replace this with actual database operations
mock_pdfs = {}


@router.post("/upload", response_model=PDFResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
):
    """Upload a new PDF document."""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a PDF"
        )

    # Save file
    try:
        filename, file_path = save_upload_file(file, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}",
        )

    # Create PDF document
    pdf_id = len(mock_pdfs) + 1
    pdf_doc = {
        "id": pdf_id,
        "title": title,
        "description": description,
        "filename": filename,
        "file_path": file_path,
        "user_id": current_user.id,
        "status": ProcessingStatus.PENDING,
        "created_at": "2023-01-01T00:00:00Z",  # Mock date
    }

    # Store in mock database
    mock_pdfs[pdf_id] = pdf_doc

    # In a real app, you would queue the PDF for processing here
    # For demo, we'll just set it to completed
    pdf_doc["status"] = ProcessingStatus.COMPLETED
    pdf_doc["page_count"] = 10  # Mock page count

    return pdf_doc


@router.get("/list", response_model=List[PDFResponse])
async def list_pdfs(current_user: User = Depends(get_current_user)):
    """List all PDFs uploaded by the current user."""
    user_pdfs = [pdf for pdf in mock_pdfs.values() if pdf["user_id"] == current_user.id]
    return user_pdfs


@router.get("/{pdf_id}", response_model=PDFResponse)
async def get_pdf(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Get PDF document details."""
    # Check if PDF exists
    if pdf_id not in mock_pdfs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

    pdf = mock_pdfs[pdf_id]

    # Check if user owns the PDF
    if pdf["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    return pdf


@router.get("/{pdf_id}/content")
async def get_pdf_content(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Get processed PDF content."""
    # Check if PDF exists
    if pdf_id not in mock_pdfs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

    pdf = mock_pdfs[pdf_id]

    # Check if user owns the PDF
    if pdf["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Check if processing is complete
    if pdf["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF processing not complete. Current status: {pdf['status']}",
        )

    # Return mock content
    return {
        "text": "This is the extracted text from the PDF.",
        "pages": [
            {"page_number": 1, "text": "Page 1 content.", "images": []},
            {"page_number": 2, "text": "Page 2 content.", "images": []},
        ],
    }


@router.get("/{pdf_id}/summary")
async def get_pdf_summary(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Get PDF summary."""
    # Check if PDF exists
    if pdf_id not in mock_pdfs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

    pdf = mock_pdfs[pdf_id]

    # Check if user owns the PDF
    if pdf["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Check if processing is complete
    if pdf["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF processing not complete. Current status: {pdf['status']}",
        )

    # Return mock summary
    return {
        "title": pdf["title"],
        "key_points": ["Key point 1", "Key point 2", "Key point 3"],
        "summary": "This is a summary of the PDF content.",
    }


@router.delete("/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Delete a PDF document."""
    # Check if PDF exists
    if pdf_id not in mock_pdfs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

    pdf = mock_pdfs[pdf_id]

    # Check if user owns the PDF
    if pdf["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Delete file if it exists
    if os.path.exists(pdf["file_path"]):
        os.remove(pdf["file_path"])

    # Remove from mock database
    del mock_pdfs[pdf_id]

    return None
