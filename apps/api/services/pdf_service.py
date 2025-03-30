import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

# Correct imports for marker-pdf package
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from models.pdf import PDFPage, PDFSummary, ProcessingStatus
from utils.pdf_utils import get_images_for_page, save_image, save_table_as_image

from config import settings

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
    async def process_pdf(file_path: str) -> Tuple[int, str, List[Dict], PDFSummary]:
        """
        Process a PDF file using marker.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple containing:
            - Page count
            - Extracted text (in markdown format)
            - List of page data
            - Summary
        """
        # Create a unique ID for this PDF processing
        pdf_id = os.path.basename(file_path).split(".")[0]
        if not pdf_id:
            pdf_id = uuid.uuid4().hex[:8]

        # Create output directory for images
        image_dir = os.path.join(settings.PDF_TEMP_DIR, pdf_id)
        os.makedirs(image_dir, exist_ok=True)

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
        markdown_text, metadata, extracted_images = text_from_rendered(rendered)

        # Get page count from metadata if available, otherwise estimate
        page_count = metadata.get("num_pages", 0) if metadata else 0
        if not page_count and hasattr(rendered, "children"):
            page_count = len(rendered.children)

        # Process pages - split markdown by page markers
        pages = []

        # If the markdown has page markers, split by them
        page_splits = []
        if "\n\n{PAGE_" in markdown_text:
            # Split by page markers like {PAGE_0}, {PAGE_1}, etc.
            import re

            page_splits = re.split(r"\n\n\{PAGE_\d+\}[\s\-*]*\n\n", markdown_text)
            # Remove empty splits
            page_splits = [p for p in page_splits if p.strip()]
        else:
            # If no page markers, treat as single page
            page_splits = [markdown_text]

        # Create page data structures
        for i, page_content in enumerate(page_splits):
            page_num = i + 1

            # Get images for this page
            page_images = []
            if extracted_images:
                # Filter images that belong to this page
                page_images = [
                    img
                    for img in extracted_images
                    if metadata and metadata.get("page_number") == page_num
                ]

            # Save image paths
            image_paths = []
            for idx, img_data in enumerate(page_images):
                img_path = os.path.join(image_dir, f"page_{page_num}_img_{idx}.png")
                with open(img_path, "wb") as f:
                    f.write(img_data)
                image_paths.append(img_path)

            # Create page data
            page_data = {
                "page_number": page_num,
                "text": page_content,
                "images": image_paths,
            }
            pages.append(page_data)

        # Generate summary
        summary = PDFSummary(
            title=os.path.basename(file_path),
            key_points=["Converted to markdown with marker"],
            summary=f"PDF with {page_count} pages processed and converted to markdown",
        )

        return page_count, markdown_text, pages, summary
