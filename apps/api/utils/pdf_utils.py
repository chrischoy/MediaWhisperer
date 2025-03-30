import io
import os
import uuid
from typing import Dict, List, Optional, Tuple

from PIL import Image

from config import settings


def save_image(image_data: bytes, page_number: int, pdf_id: str) -> str:
    """
    Save an image extracted from a PDF to disk.

    Args:
        image_data: The binary image data
        page_number: The page number the image was extracted from
        pdf_id: Identifier for the PDF the image belongs to

    Returns:
        Path to the saved image
    """
    # Create directory for this PDF's images if it doesn't exist
    image_dir = os.path.join(settings.PDF_TEMP_DIR, pdf_id)
    os.makedirs(image_dir, exist_ok=True)

    # Generate a unique filename
    image_id = uuid.uuid4().hex[:8]
    filename = f"page_{page_number}_image_{image_id}.png"
    file_path = os.path.join(image_dir, filename)

    # Save the image
    try:
        with open(file_path, "wb") as f:
            f.write(image_data)
        return file_path
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return ""


def save_table_as_image(table_data: Dict, page_number: int, pdf_id: str) -> str:
    """
    Render a complex table as an image and save it to disk.

    Args:
        table_data: Data representing the table
        page_number: The page number the table was extracted from
        pdf_id: Identifier for the PDF the table belongs to

    Returns:
        Path to the saved image
    """
    # Create directory for this PDF's images if it doesn't exist
    image_dir = os.path.join(settings.PDF_TEMP_DIR, pdf_id)
    os.makedirs(image_dir, exist_ok=True)

    # Generate a unique filename
    table_id = uuid.uuid4().hex[:8]
    filename = f"page_{page_number}_table_{table_id}.png"
    file_path = os.path.join(image_dir, filename)

    # Here we would normally render the table as an image
    # For this example, we're just creating a placeholder
    # In a real implementation, you might use libraries like:
    # - matplotlib to render tables
    # - html2image to render HTML tables as images
    # - reportlab to render tables

    # Create a simple placeholder image with text
    width, height = 400, 200
    img = Image.new("RGB", (width, height), color=(255, 255, 255))

    # Save the image
    try:
        img.save(file_path)
        return file_path
    except Exception as e:
        print(f"Error saving table image: {str(e)}")
        return ""


def get_images_for_page(pdf_id: str, page_number: int) -> List[str]:
    """
    Get all images for a specific page of a PDF.

    Args:
        pdf_id: Identifier for the PDF
        page_number: The page number to get images for

    Returns:
        List of paths to images
    """
    image_dir = os.path.join(settings.PDF_TEMP_DIR, pdf_id)

    if not os.path.exists(image_dir):
        return []

    images = []
    prefix = f"page_{page_number}_"

    for filename in os.listdir(image_dir):
        if filename.startswith(prefix) and any(
            filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg"]
        ):
            images.append(os.path.join(image_dir, filename))

    return images


def cleanup_pdf_images(pdf_id: str) -> None:
    """
    Clean up all images for a PDF.

    Args:
        pdf_id: Identifier for the PDF
    """
    image_dir = os.path.join(settings.PDF_TEMP_DIR, pdf_id)

    if os.path.exists(image_dir):
        for filename in os.listdir(image_dir):
            file_path = os.path.join(image_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {str(e)}")

        try:
            os.rmdir(image_dir)
        except Exception as e:
            print(f"Error removing directory {image_dir}: {str(e)}")
