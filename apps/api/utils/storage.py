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


def save_upload_file(upload_file: UploadFile, user_id: int) -> Tuple[str, str]:
    """
    Save an uploaded file to disk.

    Args:
        upload_file: The uploaded file
        user_id: The ID of the user uploading the file

    Returns:
        Tuple containing:
        - The file name (with UUID to avoid collisions)
        - The file path where it was saved
    """
    # Create user directory if it doesn't exist
    user_dir = os.path.join(settings.UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)

    # Generate unique filename
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"

    # Create the file path
    file_path = os.path.join(user_dir, unique_filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return unique_filename, file_path


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
