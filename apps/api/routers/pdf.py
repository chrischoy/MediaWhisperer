import json
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

# Mock database file path
MOCK_DB_PATH = os.path.join(settings.UPLOAD_DIR, "mock_pdfs.json")

# Initialize mock database from file or create empty one
if os.path.exists(MOCK_DB_PATH):
    try:
        with open(MOCK_DB_PATH, "r") as f:
            mock_pdfs = json.load(f)
        print(f"Loaded {len(mock_pdfs)} mock PDFs from {MOCK_DB_PATH}")
    except Exception as e:
        print(f"Error loading mock database: {e}")
        mock_pdfs = {}
else:
    mock_pdfs = {}
    print(f"Created new mock database at {MOCK_DB_PATH}")


# Helper function to save mock database to file
def save_mock_db():
    """Save mock database to file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(MOCK_DB_PATH), exist_ok=True)

        with open(MOCK_DB_PATH, "w") as f:
            json.dump(mock_pdfs, f)
        print(f"Saved {len(mock_pdfs)} mock PDFs to {MOCK_DB_PATH}")
    except Exception as e:
        print(f"Error saving mock database: {e}")


# Helper function to get the PDF detail file path
def get_pdf_detail_path(pdf_id, user_id, base_filename=None):
    """Get the path to the PDF detail JSON file."""
    if base_filename:
        base_name = os.path.splitext(base_filename)[0]
    else:
        base_name = f"pdf_{pdf_id}"

    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    return os.path.join(user_dir, f"{base_name}_detail.json")


# Helper function to save PDF details to a separate file
def save_pdf_details(pdf_id, details):
    """Save PDF details to a separate JSON file."""
    if pdf_id not in mock_pdfs:
        return

    pdf_meta = mock_pdfs[pdf_id]
    user_id = pdf_meta.get("user_id")
    filename = pdf_meta.get("filename")

    detail_path = get_pdf_detail_path(pdf_id, user_id, filename)

    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(detail_path), exist_ok=True)

        with open(detail_path, "w") as f:
            json.dump(details, f)
        print(f"Saved PDF details to {detail_path}")

        # Update the metadata with the detail file path
        pdf_meta["detail_path"] = detail_path
        save_mock_db()

    except Exception as e:
        print(f"Error saving PDF details: {e}")


# Helper function to load PDF details from a separate file
def load_pdf_details(pdf_id):
    """Load PDF details from a separate JSON file."""
    if pdf_id not in mock_pdfs:
        return None

    pdf_meta = mock_pdfs[pdf_id]
    detail_path = pdf_meta.get("detail_path")

    if not detail_path or not os.path.exists(detail_path):
        return None

    try:
        with open(detail_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading PDF details: {e}")
        return None


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

    # Create PDF document metadata
    pdf_id = len(mock_pdfs) + 1
    pdf_meta = {
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
    mock_pdfs[pdf_id] = pdf_meta
    save_mock_db()

    # Process the PDF using marker-pdf
    try:
        pdf_meta["status"] = ProcessingStatus.PROCESSING
        save_mock_db()

        # Process PDF with marker-pdf
        (
            page_count,
            extracted_text,
            pages,
            summary,
        ) = await PDFProcessingService.process_pdf(file_path)

        # Create detailed content for separate file
        pdf_details = {
            "page_count": page_count,
            "extracted_text": extracted_text,
            "pages": pages,
            "summary": summary,
        }

        # Save detailed content to separate file
        save_pdf_details(pdf_id, pdf_details)

        # Update basic metadata
        pdf_meta["status"] = ProcessingStatus.COMPLETED
        pdf_meta["page_count"] = page_count
        save_mock_db()

    except Exception as e:
        pdf_meta["status"] = ProcessingStatus.FAILED
        save_mock_db()
        print(f"Error processing PDF: {str(e)}")

    # Combine metadata and details for the response
    pdf_details = load_pdf_details(pdf_id) or {}
    response_data = {**pdf_meta, **pdf_details}

    return response_data


@router.post(
    "/from-url", response_model=PDFResponse, status_code=status.HTTP_201_CREATED
)
async def process_pdf_from_url(
    pdf_data: PDFFromURL,
    current_user: User = Depends(get_current_user),
):
    """Process a PDF from a URL."""
    url = pdf_data.url

    # Handle arXiv URLs specially - they should end with .pdf
    if "arxiv.org" in url.lower() and not url.lower().endswith(".pdf"):
        # If it's an arXiv URL not ending with .pdf, add it
        if "/pdf/" in url and not url.endswith(".pdf"):
            url = f"{url}.pdf"
        # Convert /abs/ URLs to /pdf/ URLs
        elif "/abs/" in url:
            # Extract the arXiv ID from the URL
            parts = url.split("/abs/")
            if len(parts) == 2:
                arxiv_id = parts[1]
                url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    # Now validate the URL
    if not url.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must point to a PDF file",
        )

    # Download the PDF
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # Raise an exception for bad responses

        # Check if the content is actually a PDF
        content_type = response.headers.get("Content-Type", "")
        if "application/pdf" not in content_type and not url.lower().endswith(".pdf"):
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
        filename = os.path.basename(url)
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
                    url_path = url.split("/")
                    path_parts = [
                        part
                        for part in url_path
                        if part and not part.startswith("http")
                    ]
                    if len(path_parts) >= 2:
                        title = f"PDF from {path_parts[-2]}"
                    else:
                        title = f"PDF from URL {len(mock_pdfs) + 1}"
                except Exception as e:
                    print(f"Error generating title: {e}")
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

        # Create PDF document metadata
        pdf_id = len(mock_pdfs) + 1
        pdf_meta = {
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
        mock_pdfs[pdf_id] = pdf_meta
        save_mock_db()

        # Process the PDF using marker-pdf
        try:
            pdf_meta["status"] = ProcessingStatus.PROCESSING
            save_mock_db()

            # Process PDF with marker-pdf
            (
                page_count,
                extracted_text,
                pages,
                summary,
            ) = await PDFProcessingService.process_pdf(permanent_path)

            # Create detailed content for separate file
            pdf_details = {
                "page_count": page_count,
                "extracted_text": extracted_text,
                "pages": pages,
                "summary": summary,
            }

            # Save detailed content to separate file
            save_pdf_details(pdf_id, pdf_details)

            # Update basic metadata
            pdf_meta["status"] = ProcessingStatus.COMPLETED
            pdf_meta["page_count"] = page_count
            save_mock_db()

        except Exception as e:
            pdf_meta["status"] = ProcessingStatus.FAILED
            save_mock_db()
            print(f"Error processing PDF from URL: {str(e)}")

        # Combine metadata and details for the response
        pdf_details = load_pdf_details(pdf_id) or {}
        response_data = {**pdf_meta, **pdf_details}

        return response_data

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
    print(f"User {current_user.id} requesting PDF list")
    print(f"Total PDFs in mock database: {len(mock_pdfs)}")

    user_pdfs = [pdf for pdf in mock_pdfs.values() if pdf["user_id"] == current_user.id]
    print(f"Found {len(user_pdfs)} PDFs for user {current_user.id}")

    return user_pdfs


@router.get("/{pdf_id}", response_model=PDFResponse)
async def get_pdf(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Get PDF document details."""
    # Check if PDF exists
    if pdf_id not in mock_pdfs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

    pdf_meta = mock_pdfs[pdf_id]

    # Check if user owns the PDF
    if pdf_meta["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Load details from separate file
    pdf_details = load_pdf_details(pdf_id)

    # Combine metadata and details
    response_data = {**pdf_meta, **pdf_details}

    return response_data


@router.get("/{pdf_id}/content")
async def get_pdf_content(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Get processed PDF content in markdown format."""
    # Check if PDF exists
    if pdf_id not in mock_pdfs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

    pdf_meta = mock_pdfs[pdf_id]

    # Check if user owns the PDF
    if pdf_meta["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Check if processing is complete
    if pdf_meta["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF processing not complete. Current status: {pdf_meta['status']}",
        )

    # Load details from separate file
    pdf_details = load_pdf_details(pdf_id)

    # Return actual content if available
    if pdf_details and "extracted_text" in pdf_details and "pages" in pdf_details:
        return {
            "text": pdf_details["extracted_text"],
            "pages": pdf_details["pages"],
        }

    # Fallback to mock content (for development only)
    return {
        "text": "# Sample PDF Content for Development\n\nThis is the extracted text from the PDF in markdown format. If you are seeing this, it means the PDF was not processed correctly.",  # noqa: E501
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

    pdf_meta = mock_pdfs[pdf_id]

    # Check if user owns the PDF
    if pdf_meta["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Check if processing is complete
    if pdf_meta["status"] != ProcessingStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"PDF processing not complete. Current status: {pdf_meta['status']}",
        )

    # Load details from separate file
    pdf_details = load_pdf_details(pdf_id)

    # Return actual summary if available
    if pdf_details and "summary" in pdf_details:
        return pdf_details["summary"]

    # Fallback to mock summary
    return {
        "title": pdf_meta["title"],
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

    pdf_meta = mock_pdfs[pdf_id]

    # Check if user owns the PDF
    if pdf_meta["user_id"] != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Delete file if it exists
    if os.path.exists(pdf_meta["file_path"]):
        os.remove(pdf_meta["file_path"])

    # Delete detail file if it exists
    if "detail_path" in pdf_meta and os.path.exists(pdf_meta["detail_path"]):
        os.remove(pdf_meta["detail_path"])

    # Clean up any extracted images
    pdf_basename = os.path.basename(pdf_meta["file_path"]).split(".")[0]
    cleanup_pdf_images(pdf_basename)

    # Remove from mock database
    del mock_pdfs[pdf_id]

    # After updating mock_pdfs
    save_mock_db()

    return None
