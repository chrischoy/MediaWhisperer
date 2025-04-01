import os
import shutil
import uuid
from typing import Optional, Tuple

from fastapi import UploadFile

from config import settings


def create_upload_directories():
    """Create necessary directories for file uploads."""
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.PDF_TEMP_DIR, exist_ok=True)


def save_upload_file(
    upload_file: UploadFile, user_id: int, pdf_id: Optional[int] = None
) -> Tuple[str, str]:
    """
    Save an uploaded file to disk.

    Args:
        upload_file: The uploaded file
        user_id: The ID of the user uploading the file
        pdf_id: Optional ID of the PDF for directory structure

    Returns:
        Tuple containing:
        - The file name (with UUID to avoid collisions)
        - The file path where it was saved
    """
    # Create user directory if it doesn't exist
    user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)

    # If pdf_id is provided, create a specific PDF directory
    if pdf_id is not None:
        pdf_dir = os.path.join(user_dir, f"pdf_{pdf_id}")
        os.makedirs(pdf_dir, exist_ok=True)
        target_dir = pdf_dir
    else:
        target_dir = user_dir

    # If the original filename was passed, use it, otherwise generate a unique name
    original_filename = upload_file.filename
    if not original_filename or original_filename.lower() == "file":
        file_extension = ".pdf"  # Default to PDF if no filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
    else:
        # Use the original filename but ensure it's safe
        unique_filename = secure_filename(original_filename)

    # Create the absolute file path
    file_path = os.path.abspath(os.path.join(target_dir, unique_filename))

    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return unique_filename, file_path


def secure_filename(filename: str) -> str:
    """
    Return a secure version of a filename that is safe for file systems.
    """
    # Get base name in case full path was provided
    filename = os.path.basename(filename)

    # Replace spaces with underscores and remove other problematic characters
    filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
    filename = filename.replace(" ", "_")

    # Ensure the filename is not empty
    if not filename:
        filename = f"file_{uuid.uuid4().hex[:8]}"

    return filename


def delete_file(file_path: str) -> bool:
    """
    Delete a file from disk.

    Args:
        file_path: Path to the file to delete

    Returns:
        True if successful, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False
