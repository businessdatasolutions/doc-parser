"""
Pydantic models for document management.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator


class ProcessingStatus(str, Enum):
    """Document processing status enumeration."""
    UPLOADED = "uploaded"
    PARSING = "parsing"
    SUMMARIZING = "summarizing"
    INDEXING = "indexing"
    READY = "ready"
    FAILED = "failed"


class DocumentCategory(str, Enum):
    """Document category enumeration."""
    MAINTENANCE = "maintenance"
    OPERATIONS = "operations"
    SPARE_PARTS = "spare_parts"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    category: DocumentCategory
    machine_model: Optional[str] = None
    part_numbers: Optional[List[str]] = Field(default_factory=list)

    @validator('category', pre=True)
    def validate_category(cls, v):
        """Validate and normalize category."""
        if isinstance(v, str):
            # Convert to lowercase and handle underscores
            v = v.lower().replace(' ', '_')
            if v not in [cat.value for cat in DocumentCategory]:
                raise ValueError(
                    f'Category must be one of: {[cat.value for cat in DocumentCategory]}'
                )
        return v

    class Config:
        use_enum_values = True


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    filename: str
    status: ProcessingStatus
    upload_date: datetime
    message: str = "Document uploaded successfully and queued for processing"

    class Config:
        use_enum_values = True


class DocumentMetadata(BaseModel):
    """Document metadata model."""
    document_id: str
    filename: str
    file_size: int  # Bytes
    file_path: str
    category: DocumentCategory
    machine_model: Optional[str] = None
    part_numbers: List[str] = Field(default_factory=list)
    upload_date: datetime
    processing_status: ProcessingStatus
    indexed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    total_pages: Optional[int] = None

    class Config:
        use_enum_values = True
        from_attributes = True  # For SQLAlchemy models


class DocumentStatusResponse(BaseModel):
    """Response model for document status check."""
    document_id: str
    filename: str
    status: ProcessingStatus
    upload_date: datetime
    indexed_at: Optional[datetime] = None
    total_pages: Optional[int] = None
    error_message: Optional[str] = None

    class Config:
        use_enum_values = True


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    total: int
    page: int
    page_size: int
    documents: List[DocumentMetadata]


class DocumentPage(BaseModel):
    """Model for a document page chunk."""
    document_id: str
    filename: str
    page: int
    content: str
    summary: Optional[str] = None
    category: DocumentCategory
    machine_model: Optional[str] = None
    part_numbers: List[str] = Field(default_factory=list)
    upload_date: datetime
    indexed_at: Optional[datetime] = None
    file_size: int
    file_path: str
    processing_status: ProcessingStatus = ProcessingStatus.READY

    class Config:
        use_enum_values = True


class ProcessingProgress(BaseModel):
    """Model for tracking document processing progress."""
    document_id: str
    current_stage: ProcessingStatus
    total_pages: Optional[int] = None
    pages_processed: int = 0
    started_at: datetime
    error_message: Optional[str] = None

    class Config:
        use_enum_values = True
