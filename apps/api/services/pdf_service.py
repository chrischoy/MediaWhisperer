import asyncio
import os
import re
import shutil
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Correct imports for marker-pdf package
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from models.pdf import PDFPage, PDFSummary, ProcessingStatus
from PIL import Image
from utils.logger import get_logger
from utils.pdf_utils import get_images_for_page, save_image, save_table_as_image

from config import settings

logger = get_logger(__name__)

# In a real application, you would use a PDF processing library
# For demonstration, this is a mock service


class PDFProcessor:
    """Service for processing PDF documents."""

    @staticmethod
    async def process_pdf(file_path: str) -> Dict[str, Any]:
        """
        Process a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing processed PDF data
        """
        # Simulate processing time
        await asyncio.sleep(2)

        # Mock result data
        return {
            "page_count": 10,
            "text": "This is the extracted text from the PDF document.",
            "pages": [
                {"page_number": i, "text": f"Content of page {i}", "images": []}
                for i in range(1, 11)
            ],
        }

    @staticmethod
    async def extract_text(file_path: str) -> str:
        """
        Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Extracted text
        """
        # Simulate processing time
        await asyncio.sleep(1)

        # Mock extracted text
        return "This is the extracted text from the PDF document."

    @staticmethod
    async def extract_images(file_path: str) -> List[str]:
        """
        Extract images from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of paths to extracted images
        """
        # Simulate processing time
        await asyncio.sleep(1)

        # Mock extracted images
        return []

    @staticmethod
    async def generate_summary(text: str) -> Dict[str, Any]:
        """
        Generate a summary of PDF content.

        Args:
            text: Extracted text from the PDF

        Returns:
            Dictionary with summary information
        """
        # Simulate processing time
        await asyncio.sleep(2)

        # Mock summary
        return {
            "title": "PDF Document",
            "key_points": ["Key point 1", "Key point 2", "Key point 3"],
            "summary": "This is a summary of the PDF content.",
        }


class PDFProcessingService:
    """Service for processing PDF documents using marker."""

    @staticmethod
    async def process_pdf(
        file_path: str, pdf_id: int = None, user_id: int = None
    ) -> Tuple[str, List[str], PDFSummary]:
        """
        Process a PDF file using marker.

        Args:
            file_path: Path to the PDF file
            pdf_id: ID of the PDF in the database (used for directory naming)
            user_id: ID of the user who uploaded the PDF

        Returns:
            Tuple containing:
            - Path to the markdown file
            - List of image paths
            - Summary
        """
        # Ensure we're working with absolute paths
        file_path = os.path.abspath(file_path)
        logger.debug(f"Processing PDF: {file_path}")

        # Use the provided PDF ID or generate one from the filename
        if pdf_id is None:
            # Legacy behavior - generate ID from filename (not recommended)
            basename = os.path.basename(file_path).split(".")[0]
            pdf_id = basename if basename else uuid.uuid4().hex[:8]

        if user_id is None:
            logger.error(f"User ID not provided for PDF: {file_path}")

        # Create directory structure: settings.UPLOAD_DIR/user_{user_id}/pdf_{pdf_id}
        user_dir = os.path.join(settings.UPLOAD_DIR, f"user_{user_id}")
        pdf_dir = os.path.join(user_dir, f"pdf_{pdf_id}")

        # Ensure directories exist
        os.makedirs(pdf_dir, exist_ok=True)

        if not file_path.startswith(os.path.abspath(pdf_dir)):
            # This case should ideally not happen if save_upload_file works correctly.
            logger.warning(
                f"PDF file {file_path} is not in the expected directory {pdf_dir}. Proceeding anyway."
            )
            # Optional: You could raise an error or attempt to copy/move if this scenario is possible.
            # For now, we'll assume save_upload_file places it correctly.

        try:
            # Use the marker library to convert the PDF to markdown
            converter = PdfConverter(
                artifact_dict=create_model_dict(),
                config={
                    "output_format": settings.MARKER_OUTPUT_FORMAT or "markdown",
                    "output_dir": pdf_dir,
                    # Set use_llm to False explicitly to avoid validation errors
                    "use_llm": False,
                },
            )

            logger.debug(f"Loaded converter")
            # Convert the PDF
            rendered = converter(file_path)
            logger.debug(f"Rendered PDF")

            # Extract text and images from the rendered result
            markdown_text, _, extracted_images = text_from_rendered(rendered)
            logger.debug(f"Extracted text")
            # extracted_images is a Dict[str, PIL.Image.Image]
            logger.info(f"Extracted text (first 1000 chars): {markdown_text[:1000]}")

            # Save the markdown text to a markdown file
            markdown_path = os.path.join(pdf_dir, f"{pdf_id}.md")
            with open(markdown_path, "w") as f:
                f.write(markdown_text)

            # Get images for this page - add proper type checking
            image_paths = []
            for figure_name, figure_pil_img in extracted_images.items():
                # Save the PIL image and add path to page_images
                img_path = os.path.join(pdf_dir, figure_name)
                image_paths.append(img_path)
                # Save the PIL image
                assert isinstance(figure_pil_img, Image.Image)
                figure_pil_img.save(img_path)
                logger.info(f"Saved image to {img_path}")

            # Extract the title from the markdown text. The first line starts with # <title>
            title = re.search(r"# (.*)", markdown_text).group(1)
            # remove <span ...>...</span> tag from the title
            title = re.sub(r"<span[^>]*>", "", title)
            title = re.sub(r"</span>", "", title)

            # TODO: AI generated key points, summary
            # Use Abstract if it is an arxiv paper

            # Generate summary
            summary = PDFSummary(
                title=title,
                key_points=["Converted to markdown with marker"],
                summary=f"PDF processed and converted to markdown",
            )

            return markdown_path, image_paths, summary

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            # Return minimal data to avoid breaking the API
            return (
                1,
                f"Error processing PDF: {str(e)}",
                [{"page_number": 1, "text": "Processing error", "images": []}],
                PDFSummary(
                    title=f"Error processing {os.path.abspath(file_path)}",
                    key_points=["Error during processing"],
                    summary="The PDF could not be processed properly. Please try again or contact support.",  # noqa: E501
                ),
            )
