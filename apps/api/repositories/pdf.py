from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..database.models import PDFDocument, PDFPage, PDFImage
from ..models.pdf import PDFCreate, PDFUpdate, ProcessingStatus
from .base import BaseRepository


class PDFRepository(BaseRepository[PDFDocument, PDFCreate, PDFUpdate]):
    """Repository for PDF document operations."""

    def __init__(self):
        super().__init__(PDFDocument)

    def get_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[PDFDocument]:
        """Get all PDFs for a specific user."""
        return (
            db.query(PDFDocument)
            .filter(PDFDocument.user_id == user_id)
            .order_by(desc(PDFDocument.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_path(self, db: Session, file_path: str) -> Optional[PDFDocument]:
        """Get a PDF by file path."""
        return db.query(PDFDocument).filter(PDFDocument.file_path == file_path).first()

    def update_status(self, db: Session, pdf_id: int, status: ProcessingStatus) -> Optional[PDFDocument]:
        """Update the processing status of a PDF."""
        pdf = self.get(db, pdf_id)
        if not pdf:
            return None
        
        pdf.status = status
        db.add(pdf)
        db.commit()
        db.refresh(pdf)
        return pdf

    def update_summary(self, db: Session, pdf_id: int, summary: str) -> Optional[PDFDocument]:
        """Update the summary of a PDF."""
        pdf = self.get(db, pdf_id)
        if not pdf:
            return None
        
        pdf.summary = summary
        db.add(pdf)
        db.commit()
        db.refresh(pdf)
        return pdf

    def add_page(self, db: Session, pdf_id: int, page_number: int, text: str) -> PDFPage:
        """Add a page to a PDF document."""
        page = PDFPage(
            pdf_id=pdf_id,
            page_number=page_number,
            text=text,
        )
        db.add(page)
        db.commit()
        db.refresh(page)
        return page

    def add_image(
        self, db: Session, pdf_id: int, page_number: int, image_path: str, width: int = None, height: int = None
    ) -> PDFImage:
        """Add an image to a PDF document."""
        image = PDFImage(
            pdf_id=pdf_id,
            page_number=page_number,
            image_path=image_path,
            width=width,
            height=height,
        )
        db.add(image)
        db.commit()
        db.refresh(image)
        return image

    def get_pages(self, db: Session, pdf_id: int) -> List[PDFPage]:
        """Get all pages for a PDF document ordered by page number."""
        return (
            db.query(PDFPage)
            .filter(PDFPage.pdf_id == pdf_id)
            .order_by(PDFPage.page_number)
            .all()
        )

    def get_images(self, db: Session, pdf_id: int) -> List[PDFImage]:
        """Get all images for a PDF document ordered by page number."""
        return (
            db.query(PDFImage)
            .filter(PDFImage.pdf_id == pdf_id)
            .order_by(PDFImage.page_number)
            .all()
        )


# Create a singleton instance
pdf_repository = PDFRepository()