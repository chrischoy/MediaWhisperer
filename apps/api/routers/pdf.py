import glob
import json
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from dependencies import get_current_user
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from models.pdf import PDFCreate, PDFDocument, PDFFromURL, PDFResponse, ProcessingStatus
from models.user import User
from services.pdf_service import PDFProcessingService
from utils.json_parser import safe_load_json
from utils.logger import get_logger
from utils.pdf_utils import cleanup_pdf_images
from utils.storage import save_upload_file

from config import settings

logger = get_logger(__name__)
router = APIRouter()

# Mock database file path
MOCK_DB_PATH = os.path.join(settings.UPLOAD_DIR, "mock_pdfs.json")

# Initialize mock database from file or create empty one
if os.path.exists(MOCK_DB_PATH):
    try:
        with open(MOCK_DB_PATH, "r") as f:
            loaded_data = json.load(f)

            # Convert string keys to integers
            mock_pdfs = {}
            for key, value in loaded_data.items():
                try:
                    # Try to convert key to integer
                    int_key = int(key)
                    mock_pdfs[int_key] = value
                except ValueError:
                    # If not convertible, keep as string
                    mock_pdfs[key] = value

        logger.info(f"Loaded {len(mock_pdfs)} mock PDFs from {MOCK_DB_PATH}")
        logger.info(f"PDF keys: {list(mock_pdfs.keys())}")
    except Exception as e:
        logger.error(f"Error loading mock database: {e}")
        mock_pdfs = {}
else:
    mock_pdfs = {}
    logger.info(f"Created new mock database at {MOCK_DB_PATH}")


# Helper function to save mock database to file
def save_mock_db():
    """Save mock database to file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(MOCK_DB_PATH), exist_ok=True)

        with open(MOCK_DB_PATH, "w") as f:
            json.dump(mock_pdfs, f)
        logger.info(f"Saved {len(mock_pdfs)} mock PDFs to {MOCK_DB_PATH}")
    except Exception as e:
        logger.error(f"Error saving mock database: {e}")


# Helper function to normalize file paths for consistent storage and retrieval
def normalize_path(path):
    """Convert relative path to absolute if needed."""
    if path and not os.path.isabs(path):
        return os.path.abspath(os.path.join(os.path.dirname(settings.UPLOAD_DIR), path))
    return path


# Helper function to get the PDF detail file path
def get_pdf_detail_path(pdf_id, user_id, base_filename=None):
    """Get the path to the PDF detail JSON file."""
    if base_filename:
        base_name = os.path.splitext(base_filename)[0]
    else:
        base_name = f"pdf_{pdf_id}"

    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    return os.path.join(user_dir, f"{base_name}_detail.json")


# Helper function to load PDF details from a separate file
def load_pdf_details(pdf_id, user_id=None) -> Optional[Dict[str, Any]]:
    """Load PDF details from the upload folder using the new directory structure."""
    # Check if this is a legacy call without user_id
    if user_id is None and pdf_id in mock_pdfs:
        user_id = mock_pdfs[pdf_id].get("user_id", 1)

    logger.info(f"Loading PDF details for PDF ID: {pdf_id}, User ID: {user_id}")

    # Construct directory path using the new structure
    user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{user_id}")
    pdf_dir = os.path.join(user_dir, f"pdf_{pdf_id}")

    # If directory doesn't exist, try the old path format as fallback
    if not os.path.exists(pdf_dir):
        logger.warning(
            f"PDF directory not found at new path: {pdf_dir}, trying legacy path"
        )
        pdf_dir = os.path.join(settings.UPLOAD_DIR, str(pdf_id))
        if not os.path.exists(pdf_dir):
            logger.warning(f"PDF directory not found at legacy path: {pdf_dir}")
            return None

    # Grep md and jpeg files
    md_files = glob.glob(os.path.join(pdf_dir, "*.md"))
    jpeg_files = glob.glob(os.path.join(pdf_dir, "*.jpeg"))
    logger.info(
        f"Found {len(md_files)} markdown files and {len(jpeg_files)} jpeg files"
    )

    # Load the markdown file and return the content
    pdf_markdown = None
    if md_files:
        try:
            with open(md_files[0], "r") as f:
                pdf_markdown = f.read()
        except Exception as e:
            logger.error(f"Error loading markdown file: {e}")

    # Return None if no files are found
    return {
        "markdown": pdf_markdown,
        "images": jpeg_files,
    }


# Fix existing file paths in the database at startup
for _pdf_id, pdf_meta in mock_pdfs.items():
    if "file_path" in pdf_meta:
        pdf_meta["file_path"] = normalize_path(pdf_meta["file_path"])
    if "detail_path" in pdf_meta:
        pdf_meta["detail_path"] = normalize_path(pdf_meta["detail_path"])
save_mock_db()


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

    # Generate a PDF ID
    pdf_id = len(mock_pdfs) + 1

    # Save file
    try:
        filename, file_path = save_upload_file(file, current_user.id, pdf_id)
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
            markdown_path,
            image_paths,
            summary,
        ) = await PDFProcessingService.process_pdf(file_path, pdf_id, current_user.id)

        # Create detailed content for separate file
        pdf_details = {
            "markdown_path": markdown_path,
            "image_paths": image_paths,
            "summary": summary,
        }

        # Update basic metadata
        pdf_meta["status"] = ProcessingStatus.COMPLETED
        save_mock_db()

    except Exception as e:
        pdf_meta["status"] = ProcessingStatus.FAILED
        save_mock_db()
        logger.error(f"Error processing PDF: {str(e)}")

    # Combine metadata and details for the response
    pdf_details = load_pdf_details(pdf_id, current_user.id) or {}
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
                    logger.error(f"Error generating title: {e}")
                    title = f"PDF from URL {len(mock_pdfs) + 1}"

        # Create user directory if it doesn't exist
        user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}")
        os.makedirs(user_dir, exist_ok=True)

        # Create PDF ID
        pdf_id = len(mock_pdfs) + 1

        # Create PDF-specific directory
        pdf_dir = os.path.join(user_dir, f"pdf_{pdf_id}")
        os.makedirs(pdf_dir, exist_ok=True)

        # Create permanent path (ensure it's absolute)
        permanent_path = os.path.abspath(os.path.join(pdf_dir, filename))

        # Copy temporary file to permanent location
        shutil.copy(temp_file_path, permanent_path)

        # Remove temporary file
        os.unlink(temp_file_path)

        # Create PDF document metadata
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
                markdown_path,
                image_paths,
                summary,
            ) = await PDFProcessingService.process_pdf(
                permanent_path, pdf_id, current_user.id
            )

            # Create detailed content for separate file
            pdf_details = {
                "markdown_path": markdown_path,
                "image_paths": image_paths,
                "summary": summary,
            }

            # Update basic metadata
            pdf_meta["status"] = ProcessingStatus.COMPLETED

            # For arxiv, update title to paper title
            if "arxiv.org" in url.lower():
                # Extract the paper title from the summary
                paper_title = summary.title
                pdf_meta["title"] = paper_title
            save_mock_db()

        except Exception as e:
            pdf_meta["status"] = ProcessingStatus.FAILED
            save_mock_db()
            logger.error(f"Error processing PDF from URL: {str(e)}")

        # Combine metadata and details for the response
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
    logger.info(f"User {current_user.id} requesting PDF list")
    logger.info(f"Total PDFs in mock database: {len(mock_pdfs)}")

    user_pdfs = [pdf for pdf in mock_pdfs.values() if pdf["user_id"] == current_user.id]
    logger.info(f"Found {len(user_pdfs)} PDFs for user {current_user.id}")

    return user_pdfs


@router.get("/{pdf_id}", response_model=PDFResponse)
async def get_pdf(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Get PDF document details."""
    logger.info(f"\n====== GET PDF ENDPOINT DEBUG ======")
    logger.info(f"Requested PDF ID: {pdf_id}, type: {type(pdf_id)}")
    logger.info(f"Current user: {current_user}")
    logger.info(f"Total PDFs in mock_pdfs: {len(mock_pdfs)}")
    logger.info(f"Available PDFs keys: {list(mock_pdfs.keys())}")
    logger.info(f"mock_pdfs directory: {os.path.abspath(MOCK_DB_PATH)}")

    # Get PDF by ID
    pdf_meta = mock_pdfs.get(pdf_id)

    # If file doesn't exist, raise 404
    if not pdf_meta:
        logger.info(f"File not found for PDF ID: {pdf_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

    # Check if user owns the PDF
    if pdf_meta["user_id"] != current_user.id:
        logger.info(f"User {current_user.id} does not own PDF {pdf_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
        )

    # Load details from separate file
    pdf_details = load_pdf_details(pdf_id, current_user.id)  # keys: markdown and images

    if "markdown" not in pdf_details:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF details do not contain markdown",
        )

    if "detail_path" in pdf_meta:
        logger.info(f"Detail path: {pdf_meta['detail_path']}")
        logger.info(f"Detail path exists: {os.path.exists(pdf_meta['detail_path'])}")

    # Combine metadata and details, handling the case where details might be None
    response_data = {**pdf_meta, **pdf_details}
    logger.info(f"====== END PDF ENDPOINT DEBUG ======")

    return response_data


@router.get("/{pdf_id}/images/{filename}")
async def get_pdf_image(
    pdf_id: int,
    filename: str,
):
    """Serve a specific image associated with a PDF."""
    # Basic security check for filename to prevent path traversal
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename"
        )

    # --- Look up user_id from PDF metadata ---
    pdf_meta = mock_pdfs.get(pdf_id)
    if not pdf_meta:
        # Don't reveal if PDF exists, just say image not found for security
        logger.warning(
            f"PDF metadata not found for PDF ID: {pdf_id} when requesting image: {filename}"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    user_id = pdf_meta.get("user_id")
    if not user_id:
        logger.error(f"User ID not found in PDF metadata for PDF ID: {pdf_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
    # --- End lookup ---

    # Construct the expected file path using the retrieved user_id
    user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{user_id}")
    pdf_dir = os.path.join(user_dir, f"pdf_{pdf_id}")
    file_path = os.path.join(pdf_dir, filename)

    logger.info(f"Attempting to serve image: {file_path}")

    # Check if the file exists
    if not os.path.exists(file_path):
        logger.warning(f"Image not found at path: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
        )

    # Check if it is indeed a file (and not a directory, etc.)
    if not os.path.isfile(file_path):
        logger.error(f"Requested path is not a file: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid path"
        )

    # Return the file
    return FileResponse(path=file_path)


@router.get("/{pdf_id}/content")
async def get_pdf_content(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Get processed PDF content in markdown format."""
    # Get PDF by ID
    pdf_meta = mock_pdfs.get(pdf_id)

    # Check if PDF exists
    if not pdf_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

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
    pdf_details = load_pdf_details(pdf_id, current_user.id)  # keys: markdown and images

    # Return actual content if available
    if pdf_details and "markdown" in pdf_details and "images" in pdf_details:
        return {
            "markdown": pdf_details["markdown"],
            "images": pdf_details["images"],
        }

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="PDF details do not contain markdown or images",
    )


@router.get("/{pdf_id}/summary")
async def get_pdf_summary(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Get PDF summary."""
    # Get PDF by ID
    pdf_meta = mock_pdfs.get(pdf_id)

    # Check if PDF exists
    if not pdf_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

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
    pdf_details = load_pdf_details(pdf_id, current_user.id)

    # Return actual summary if available
    if pdf_details and "summary" in pdf_details:
        return pdf_details["summary"]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="PDF summary not found",
    )


@router.delete("/{pdf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf(pdf_id: int, current_user: User = Depends(get_current_user)):
    """Delete a PDF document."""
    # Get PDF by ID
    pdf_meta = mock_pdfs.get(pdf_id)

    # Check if PDF exists
    if not pdf_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PDF not found"
        )

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

    # Clean up the PDF directory
    user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{current_user.id}")
    pdf_dir = os.path.join(user_dir, f"pdf_{pdf_id}")

    if os.path.exists(pdf_dir):
        try:
            shutil.rmtree(pdf_dir)
            logger.info(f"Removed PDF directory: {pdf_dir}")
        except Exception as e:
            logger.error(f"Error removing PDF directory: {e}")

    # Also check legacy directory structure
    legacy_pdf_dir = os.path.join(settings.UPLOAD_DIR, str(pdf_id))
    if os.path.exists(legacy_pdf_dir):
        try:
            shutil.rmtree(legacy_pdf_dir)
            logger.info(f"Removed legacy PDF directory: {legacy_pdf_dir}")
        except Exception as e:
            logger.error(f"Error removing legacy PDF directory: {e}")

    # Remove from mock database
    del mock_pdfs[pdf_id]

    # After updating mock_pdfs
    save_mock_db()

    return None
