import os
import shutil
import tempfile
from datetime import datetime
from typing import List, Optional

import requests
from dependencies import get_current_user
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from models.pdf import PDFCreate, PDFDocument, PDFFromURL, PDFResponse, ProcessingStatus
from models.user import User
from services.pdf_service import PDFProcessingService
from utils.pdf_utils import cleanup_pdf_images
from utils.storage import save_upload_file

from config import settings

router = APIRouter()

# Mock database for demonstration
# In a real app, replace this with actual database operations
mock_pdfs = {}


@router.post("/upload", response_model=PDFResponse, status_code=status.HTTP_201_CREATED)
async def upload_pdf(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
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

    # Generate title if not provided
    if not title:
        # Use the filename without extension as the title
        title = os.path.splitext(file.filename)[0]
        # If filename is just a UUID or doesn't make a good title, use a default
        if len(title) < 3 or title.startswith("file") or title.isdigit():
            title = f"PDF Document {len(mock_pdfs) + 1}"

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
        "created_at": datetime.now().isoformat(),
    }

    # Store in mock database
    mock_pdfs[pdf_id] = pdf_doc

    # Process the PDF using marker-pdf
    try:
        pdf_doc["status"] = ProcessingStatus.PROCESSING

        # Process PDF with marker-pdf
        (
            page_count,
            extracted_text,
            pages,
            summary,
        ) = await PDFProcessingService.process_pdf(file_path)

        # Update PDF document with results
        pdf_doc["status"] = ProcessingStatus.COMPLETED
        pdf_doc["page_count"] = page_count
        pdf_doc["extracted_text"] = extracted_text
        pdf_doc["pages"] = pages
        pdf_doc["summary"] = summary

    except Exception as e:
        pdf_doc["status"] = ProcessingStatus.FAILED
        print(f"Error processing PDF: {str(e)}")

    return pdf_doc


@router.post(
    "/from-url", response_model=PDFResponse, status_code=status.HTTP_201_CREATED
)
async def process_pdf_from_url(
    pdf_data: PDFFromURL,
    current_user: User = Depends(get_current_user),
):
    """Process a PDF from a URL."""
    # Validate URL (basic check)
    if not pdf_data.url.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must point to a PDF file",
        )

    # Download the PDF
    try:
        response = requests.get(pdf_data.url, stream=True, timeout=30)
        response.raise_for_status()  # Raise an exception for bad responses

        # Check if the content is actually a PDF
        content_type = response.headers.get("Content-Type", "")
        if "application/pdf" not in content_type and not pdf_data.url.lower().endswith(
            ".pdf"
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The URL does not point to a PDF file. Content-Type: {content_type}",
            )

        # Create a temporary file to store the downloaded PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file_path = temp_file.name

        # Create a filename from the URL
        filename = os.path.basename(pdf_data.url)
        if not filename:
            filename = f"url_pdf_{len(mock_pdfs) + 1}.pdf"

        # Generate title if not provided
        title = pdf_data.title
        if not title:
            # Try to use the filename without extension
            title = os.path.splitext(filename)[0]
            # If not a good title, use the last part of the URL
            if len(title) < 3 or title.isdigit():
                try:
                    url_path = pdf_data.url.split("/")
                    path_parts = [
                        part
                        for part in url_path
                        if part and not part.startswith("http")
                    ]
                    if len(path_parts) >= 2:
                        title = f"PDF from {path_parts[-2]}"
                    else:
                        title = f"PDF from URL {len(mock_pdfs) + 1}"
                except:
                    title = f"PDF from URL {len(mock_pdfs) + 1}"

        # Create user directory if it doesn't exist
        user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
        os.makedirs(user_dir, exist_ok=True)

        # Create permanent path
        permanent_path = os.path.join(user_dir, filename)

        # Copy temporary file to permanent location
        shutil.copy(temp_file_path, permanent_path)

        # Remove temporary file
        os.unlink(temp_file_path)

        # Create PDF document
        pdf_id = len(mock_pdfs) + 1
        pdf_doc = {
            "id": pdf_id,
            "title": title,
            "description": pdf_data.description,
            "filename": filename,
            "file_path": permanent_path,
            "user_id": current_user.id,
            "status": ProcessingStatus.PENDING,
            "created_at": datetime.now().isoformat(),
        }

        # Store in mock database
        mock_pdfs[pdf_id] = pdf_doc

        # Process the PDF using marker-pdf
        try:
            pdf_doc["status"] = ProcessingStatus.PROCESSING

            # Process PDF with marker-pdf
            (
                page_count,
                extracted_text,
                pages,
                summary,
            ) = await PDFProcessingService.process_pdf(permanent_path)

            # Update PDF document with results
            pdf_doc["status"] = ProcessingStatus.COMPLETED
            pdf_doc["page_count"] = page_count
            pdf_doc["extracted_text"] = extracted_text
            pdf_doc["pages"] = pages
            pdf_doc["summary"] = summary

        except Exception as e:
            pdf_doc["status"] = ProcessingStatus.FAILED
            print(f"Error processing PDF from URL: {str(e)}")

        return pdf_doc

    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to download PDF from URL: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing PDF from URL: {str(e)}",
        )


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
    """Get processed PDF content in markdown format."""
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

    # Return actual content if available, otherwise mock data
    if "extracted_text" in pdf and "pages" in pdf:
        return {
            "text": pdf["extracted_text"],  # This is now in markdown format
            "pages": pdf["pages"],  # Each page text is also in markdown
        }

    # Fallback to mock content (for development only)
    return {
        "text": "# Sample PDF Content for Development\n\nThis is the extracted text from the PDF in markdown format. If you are seeing this, it means the PDF was not processed correctly.",
        "pages": [
            {
                "page_number": 1,
                "text": "## Page 1\n\nPage 1 content in markdown.",
                "images": [],
            },
            {
                "page_number": 2,
                "text": "## Page 2\n\nPage 2 content in markdown.",
                "images": [],
            },
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

    # Return actual summary if available, otherwise mock data
    if "summary" in pdf:
        return pdf["summary"]

    # Fallback to mock summary
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

    # Clean up any extracted images
    pdf_basename = os.path.basename(pdf["file_path"]).split(".")[0]
    cleanup_pdf_images(pdf_basename)

    # Remove from mock database
    del mock_pdfs[pdf_id]

    return None
