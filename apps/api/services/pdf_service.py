import asyncio
import os
import re
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
    async def process_pdf(file_path: str) -> Tuple[str, List[str], PDFSummary]:
        """
        Process a PDF file using marker.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple containing:
            - Path to the markdown file
            - List of image paths
            - Summary
        """
        # Ensure we're working with absolute paths
        file_path = os.path.abspath(file_path)

        # Create a unique ID for this PDF processing
        pdf_id = os.path.basename(file_path).split(".")[0]
        if not pdf_id:
            pdf_id = uuid.uuid4().hex[:8]

        # Get the directory where the PDF file is stored
        pdf_dir = os.path.dirname(file_path)

        # Create output directory for images in the same directory as the PDF
        output_dir_name = f"{pdf_id}_processed"
        image_dir = os.path.join(pdf_dir, output_dir_name)
        image_dir = os.path.abspath(image_dir)
        os.makedirs(image_dir, exist_ok=True)

        try:
            # Use the marker library to convert the PDF to markdown
            converter = PdfConverter(
                artifact_dict=create_model_dict(),
                config={
                    "output_format": settings.MARKER_OUTPUT_FORMAT or "markdown",
                    "output_dir": image_dir,
                    # Set use_llm to False explicitly to avoid validation errors
                    "use_llm": False,
                },
            )

            # Convert the PDF
            rendered = converter(file_path)

            # Extract text and images from the rendered result
            markdown_text, _, extracted_images = text_from_rendered(rendered)
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

            # Generate summary
            summary = PDFSummary(
                title=os.path.basename(file_path),
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
                    title=os.path.basename(file_path),
                    key_points=["Error during processing"],
                    summary="The PDF could not be processed properly. Please try again or contact support.",  # noqa: E501
                ),
            )
