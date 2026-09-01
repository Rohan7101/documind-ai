from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.document import Document


class DocumentRepository:
    """Repository handling database operations for documents."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, document: Document) -> Document:
        """Add a new document record and commit."""
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_by_id(self, document_id: str) -> Optional[Document]:
        """Fetch a document by its ID."""
        stmt = select(Document).where(Document.id == document_id)
        return self.db.scalars(stmt).first()

    def list(self, skip: int = 0, limit: int = 20) -> tuple[list[Document], int]:
        """List documents ordered by newest first with pagination and total count."""
        total_stmt = select(func.count(Document.id))
        total = self.db.scalar(total_stmt) or 0

        stmt = (
            select(Document)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(self.db.scalars(stmt).all())
        return items, total

    def delete(self, document: Document) -> None:
        """Delete a document record from the database."""
        self.db.delete(document)
        self.db.commit()

    def update_status(self, document: Document, status: str) -> Document:
        """Update the processing status of a document."""
        document.status = status
        self.db.commit()
        self.db.refresh(document)
        return document

    def update_extraction_result(
        self,
        document: Document,
        extracted_text: Optional[str],
        status: str,
    ) -> Document:
        """Update the document extracted text and processing status."""
        document.extracted_text = extracted_text
        document.status = status
        self.db.commit()
        self.db.refresh(document)
        return document

