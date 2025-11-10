"""Document models for legal document management."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ProcessingStatus(str, Enum):
    """Document processing status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class LegalDocument(BaseModel):
    """Legal document metadata model."""

    document_id: UUID = Field(
        default_factory=uuid4,
        description="Unique identifier for the document"
    )
    title: str = Field(
        ...,
        description="Document title",
        min_length=1,
        max_length=500
    )
    file_path: str = Field(
        ...,
        description="Path to the stored document file"
    )
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.PENDING,
        description="Current processing status of the document"
    )
    uploaded_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when document was uploaded"
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when document processing completed"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if processing failed"
    )
    total_chunks: int = Field(
        default=0,
        description="Total number of chunks created from this document"
    )
    file_size_bytes: int = Field(
        default=0,
        description="File size in bytes"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    title: str = Field(
        ...,
        description="Document title",
        min_length=1,
        max_length=500
    )


class DocumentResponse(BaseModel):
    """Response model for document information."""
    document_id: UUID
    title: str
    processing_status: ProcessingStatus
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    total_chunks: int = 0
    file_size_bytes: int = 0

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
