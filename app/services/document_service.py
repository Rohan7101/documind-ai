import uuid
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import (
    DocumentNotFoundException,
    FileTooLargeException,
    InvalidFileTypeException,
    InvalidPDFException,
    UploadFailedException,
)
from app.core.logging import logger
from app.models.document import Document
from app.repositories.document_repository import DocumentRepository

PDF_MAGIC_BYTES = b"%PDF-"


class DocumentService:
    """Service orchestrating document validation, storage, and database persistence."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = DocumentRepository(db)

    def validate_file(self, filename: Optional[str], content: bytes) -> None:
        """Validate filename extension, file size, and magic bytes signature."""
        if not filename or not filename.lower().endswith(".pdf"):
            raise InvalidFileTypeException("Only PDF files (.pdf) are supported.")

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise FileTooLargeException(
                f"File size ({len(content)} bytes) exceeds the maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB."
            )

        if not content.startswith(PDF_MAGIC_BYTES):
            raise InvalidPDFException("The uploaded file does not contain a valid PDF signature.")

    @staticmethod
    def resolve_file_path(document: Document) -> Path:
        """Resolve the absolute physical filesystem path for a document from the configured STORAGE_DIR."""
        return Path(settings.STORAGE_DIR) / document.stored_filename

    def upload_document(self, filename: str, content: bytes, mime_type: Optional[str] = None) -> Document:
        """Validate, store securely on disk, and save document record in SQLite."""
        self.validate_file(filename=filename, content=content)

        # Sanitize original filename (strip directory paths) for storage in DB
        safe_original_filename = Path(filename).name or "document.pdf"

        # Generate unique identifier and collision-free stored filename
        doc_id = str(uuid.uuid4())
        stored_filename = f"{doc_id}.pdf"

        # Ensure physical storage directory exists
        storage_path = Path(settings.STORAGE_DIR)
        storage_path.mkdir(parents=True, exist_ok=True)
        file_dest = storage_path / stored_filename

        # Write file to storage
        try:
            with open(file_dest, "wb") as f:
                f.write(content)
        except Exception as err:
            logger.error(f"Error writing document to disk: {err}", exc_info=True)
            raise UploadFailedException("Failed to write document to storage.")

        # Persist metadata to database using a portable relative storage key/path
        relative_file_path = f"storage/documents/{stored_filename}"
        try:
            document = Document(
                id=doc_id,
                original_filename=safe_original_filename,
                stored_filename=stored_filename,
                file_path=relative_file_path,
                mime_type=mime_type or "application/pdf",
                file_size=len(content),
                status="uploaded",
            )
            created_doc = self.repository.create(document)
            logger.info(f"Document stored successfully: id={created_doc.id}, file={stored_filename}")
            return created_doc
        except Exception as db_err:
            # Transaction failure safety: clean up orphaned file on disk
            logger.error(f"Database error while saving document record: {db_err}. Cleaning up file.", exc_info=True)
            if file_dest.exists():
                try:
                    file_dest.unlink()
                except Exception as cleanup_err:
                    logger.warning(f"Failed to cleanup orphaned file {file_dest}: {cleanup_err}")
            raise UploadFailedException("Database failure while creating document record.")

    def get_document(self, document_id: str) -> Document:
        """Retrieve a document by ID or raise DocumentNotFoundException."""
        document = self.repository.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundException(f"Document with ID '{document_id}' not found.")
        return document

    def list_documents(self, skip: int = 0, limit: int = 20) -> tuple[list[Document], int]:
        """List documents with pagination."""
        return self.repository.list(skip=skip, limit=limit)

    def delete_document(self, document_id: str) -> None:
        """Delete a document record and its stored file."""
        document = self.get_document(document_id)

        # Delete stored physical file from disk
        file_path = self.resolve_file_path(document)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted stored file: {file_path}")
            except Exception as file_err:
                logger.warning(f"Error removing stored file {file_path}: {file_err}")

        # Delete database record
        self.repository.delete(document)
        logger.info(f"Deleted document record: id={document_id}")

