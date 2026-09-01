from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_service import DocumentService

router = APIRouter(prefix="/api/documents", tags=["Documents"])


def get_document_service(db: Session = Depends(get_db)) -> DocumentService:
    """Dependency provider for DocumentService."""
    return DocumentService(db)


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a PDF document",
    description="Validates, stores the PDF securely on the local filesystem, and records metadata in SQLite.",
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Upload and validate a PDF file."""
    content = await file.read()
    document = service.upload_document(
        filename=file.filename or "document.pdf",
        content=content,
        mime_type=file.content_type,
    )
    return DocumentResponse.model_validate(document)


@router.get(
    "",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List uploaded documents",
    description="Retrieve a paginated list of uploaded documents ordered newest first.",
)
def list_documents(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return (1-100)"),
    service: DocumentService = Depends(get_document_service),
) -> DocumentListResponse:
    """List documents with pagination."""
    items, total = service.list_documents(skip=skip, limit=limit)
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get document details",
    description="Retrieve metadata for a specific document by its unique ID.",
)
def get_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Get single document metadata."""
    document = service.get_document(document_id)
    return DocumentResponse.model_validate(document)


@router.post(
    "/{document_id}/extract",
    response_model=DocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Extract text from document",
    description="Extracts machine-readable text from the stored PDF using PyMuPDF and stores it in SQLite.",
)
def extract_document_text(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentResponse:
    """Trigger PDF text extraction for a document."""
    document = service.extract_text(document_id)
    return DocumentResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a document",
    description="Removes the document metadata from SQLite and deletes the stored file from disk.",
)
def delete_document(
    document_id: str,
    service: DocumentService = Depends(get_document_service),
) -> DocumentDeleteResponse:
    """Delete a document and its stored file."""
    service.delete_document(document_id)
    return DocumentDeleteResponse(
        message="Document deleted successfully",
        id=document_id,
    )

