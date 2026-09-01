from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    """Schema for document metadata returned by API."""

    id: str = Field(..., description="Unique identifier for the document")
    original_filename: str = Field(..., description="Original name of the uploaded file")
    stored_filename: str = Field(..., description="Secure sanitized filename stored on disk")
    mime_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., description="Size of the file in bytes")
    status: str = Field(..., description="Current processing status of the document")
    created_at: datetime = Field(..., description="Timestamp when the document was uploaded")
    updated_at: datetime = Field(..., description="Timestamp when the document was last updated")

    model_config = ConfigDict(from_attributes=True)


class DocumentListResponse(BaseModel):
    """Paginated list of document responses."""

    items: list[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total count of documents")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Maximum items per page")


class DocumentDeleteResponse(BaseModel):
    """Response schema for document deletion."""

    message: str = Field(..., description="Status message")
    id: str = Field(..., description="ID of the deleted document")
