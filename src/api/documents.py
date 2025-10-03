"""
Document management API endpoints.
"""

import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    status,
    Depends,
    BackgroundTasks,
    Query,
)
from fastapi.responses import FileResponse

from src.models.document import (
    DocumentUploadResponse,
    DocumentStatusResponse,
    DocumentListResponse,
    DocumentCategory,
    ProcessingStatus,
    DocumentMetadata,
)
from src.db.postgres import get_postgres_client
from src.db.elasticsearch import get_elasticsearch_client
from src.services.document_processor import DocumentProcessor
from src.config import settings
from src.utils.auth import verify_api_key
from src.utils.logging import get_logger
from src.utils.pdf_utils import limit_pdf_to_max_pages, cleanup_limited_pdf

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def validate_pdf_file(file: UploadFile) -> None:
    """
    Validate uploaded file is a PDF and within size limits.

    Args:
        file: Uploaded file

    Raises:
        HTTPException: If validation fails
    """
    # Check file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    # Check content type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid content type: {file.content_type}. Expected application/pdf",
        )


async def save_uploaded_file(
    file: UploadFile, document_id: str, storage_path: Path
) -> tuple[Path, int]:
    """
    Save uploaded file to storage.

    Args:
        file: Uploaded file
        document_id: Unique document ID
        storage_path: Base storage directory

    Returns:
        tuple: (file_path, file_size)

    Raises:
        HTTPException: If save fails or file too large
    """
    # Create storage directory if it doesn't exist
    storage_path.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_extension = Path(file.filename).suffix
    file_path = storage_path / f"{document_id}{file_extension}"

    # Save file and check size
    file_size = 0
    max_size = settings.max_file_size_mb * 1024 * 1024  # Convert to bytes

    try:
        with open(file_path, "wb") as f:
            while chunk := await file.read(8192):  # Read in 8KB chunks
                file_size += len(chunk)

                # Check size limit
                if file_size > max_size:
                    # Delete partial file
                    file_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB",
                    )

                f.write(chunk)

        logger.info(f"Saved file: {file_path} ({file_size} bytes)")
        return file_path, file_size

    except HTTPException:
        raise
    except Exception as e:
        # Clean up partial file
        file_path.unlink(missing_ok=True)
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        )


async def process_document_task(
    document_id: str,
    file_path: Path,
    category: DocumentCategory,
    machine_model: Optional[str] = None,
) -> None:
    """
    Background task to process uploaded document.

    Args:
        document_id: Document ID
        file_path: Path to PDF file
        category: Document category
        machine_model: Optional machine model
    """
    processor = DocumentProcessor()
    pg_client = get_postgres_client()
    limited_pdf_path = None

    try:
        # Update status to parsing
        pg_client.update_document_status(document_id, ProcessingStatus.PARSING)

        # Check PDF page count and create limited version if needed
        # This handles LandingAI's 50-page limitation
        pdf_to_process, original_page_count, was_truncated = limit_pdf_to_max_pages(file_path)

        if was_truncated:
            limited_pdf_path = pdf_to_process
            logger.warning(
                f"Document {document_id} truncated from {original_page_count} to 50 pages "
                f"due to LandingAI limitation"
            )
            # Add truncation info to error message field for user awareness
            pg_client.update_document_status(
                document_id=document_id,
                status=ProcessingStatus.PARSING,
                error_message=f"Note: PDF truncated from {original_page_count} to 50 pages for processing"
            )

        # Process document (with limited version if truncated)
        result = processor.process_document(
            file_path=pdf_to_process,
            document_id=document_id,
            category=category,
            machine_model=machine_model,
            generate_summaries=True,
        )

        # Update status to ready
        final_error_msg = None
        if was_truncated:
            final_error_msg = f"Note: Original PDF had {original_page_count} pages, processed first 50 pages only"

        pg_client.update_document_status(
            document_id=document_id,
            status=ProcessingStatus.READY,
            total_pages=result.get("total_pages"),
            indexed_at=datetime.utcnow(),
            error_message=final_error_msg
        )

        logger.info(f"Document {document_id} processed successfully")

    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {e}")

        # Update status to failed
        pg_client.update_document_status(
            document_id=document_id,
            status=ProcessingStatus.FAILED,
            error_message=str(e),
        )

    finally:
        # Clean up limited PDF if it was created
        if limited_pdf_path:
            cleanup_limited_pdf(limited_pdf_path)


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form(...),
    machine_model: Optional[str] = Form(None),
    api_key: str = Depends(verify_api_key),
) -> DocumentUploadResponse:
    """
    Upload a PDF document for processing.

    Args:
        background_tasks: FastAPI background tasks
        file: PDF file to upload
        category: Document category (maintenance, operations, spare_parts)
        machine_model: Optional machine model identifier
        api_key: API key for authentication

    Returns:
        DocumentUploadResponse: Upload response with document ID and status

    Raises:
        HTTPException: If validation fails or upload fails
    """
    # Validate file
    validate_pdf_file(file)

    # Validate category
    try:
        doc_category = DocumentCategory(category.lower().replace(" ", "_"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category. Must be one of: {[c.value for c in DocumentCategory]}",
        )

    # Generate document ID
    document_id = str(uuid.uuid4())

    # Save file
    storage_path = Path(settings.pdf_storage_path)
    file_path, file_size = await save_uploaded_file(file, document_id, storage_path)

    # Create database record
    pg_client = get_postgres_client()

    try:
        pg_client.create_document(
            document_id=document_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            category=doc_category,
            machine_model=machine_model,
        )
    except Exception as e:
        # Clean up file if database insert fails
        file_path.unlink(missing_ok=True)
        logger.error(f"Failed to create document record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document record: {str(e)}",
        )

    # Queue background processing
    background_tasks.add_task(
        process_document_task,
        document_id=document_id,
        file_path=file_path,
        category=doc_category,
        machine_model=machine_model,
    )

    logger.info(
        f"Document {document_id} uploaded and queued for processing: {file.filename}"
    )

    return DocumentUploadResponse(
        document_id=document_id,
        filename=file.filename,
        status=ProcessingStatus.UPLOADED,
        upload_date=datetime.utcnow(),
    )


@router.get("/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str, api_key: str = Depends(verify_api_key)
) -> DocumentStatusResponse:
    """
    Get document metadata and processing status.

    Args:
        document_id: Document ID
        api_key: API key for authentication

    Returns:
        DocumentStatusResponse: Document status information

    Raises:
        HTTPException: If document not found
    """
    pg_client = get_postgres_client()
    doc = pg_client.get_document(document_id)

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    return DocumentStatusResponse(
        document_id=doc.id,
        filename=doc.filename,
        status=doc.processing_status,
        upload_date=doc.upload_date,
        indexed_at=doc.indexed_at,
        total_pages=doc.total_pages,
        error_message=doc.error_message,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    doc_status: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    api_key: str = Depends(verify_api_key),
) -> DocumentListResponse:
    """
    List documents with optional filters and pagination.

    Args:
        doc_status: Optional status filter
        category: Optional category filter
        page: Page number (1-indexed)
        page_size: Items per page (max 100)
        api_key: API key for authentication

    Returns:
        DocumentListResponse: Paginated list of documents

    Raises:
        HTTPException: If validation fails
    """
    # Validate pagination
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Page must be >= 1"
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100",
        )

    # Parse filters
    status_filter = None
    if doc_status:
        try:
            status_filter = ProcessingStatus(doc_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in ProcessingStatus]}",
            )

    category_filter = None
    if category:
        try:
            category_filter = DocumentCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category. Must be one of: {[c.value for c in DocumentCategory]}",
            )

    # Get documents
    pg_client = get_postgres_client()
    offset = (page - 1) * page_size

    docs = pg_client.list_documents(
        status=status_filter, category=category_filter, limit=page_size, offset=offset
    )

    total = pg_client.count_documents(status=status_filter, category=category_filter)

    # Convert to metadata models
    document_list = []
    for doc in docs:
        document_list.append(
            DocumentMetadata(
                document_id=doc.id,
                filename=doc.filename,
                file_size=doc.file_size,
                file_path=doc.file_path,
                category=doc.category,
                machine_model=doc.machine_model,
                part_numbers=[],  # Not stored in DB currently
                upload_date=doc.upload_date,
                processing_status=doc.processing_status,
                indexed_at=doc.indexed_at,
                error_message=doc.error_message,
                total_pages=doc.total_pages,
            )
        )

    return DocumentListResponse(
        total=total, page=page, page_size=page_size, documents=document_list
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str, api_key: str = Depends(verify_api_key)
) -> None:
    """
    Delete a document and all associated data.

    Args:
        document_id: Document ID
        api_key: API key for authentication

    Raises:
        HTTPException: If document not found or deletion fails
    """
    pg_client = get_postgres_client()
    es_client = get_elasticsearch_client()

    # Get document
    doc = pg_client.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Delete from Elasticsearch
    try:
        # Delete all pages for this document
        es_client.delete_by_query(
            index="documents",
            body={"query": {"term": {"document_id.keyword": document_id}}},
        )
        logger.info(f"Deleted Elasticsearch documents for {document_id}")
    except Exception as e:
        logger.warning(f"Failed to delete from Elasticsearch: {e}")
        # Continue with deletion even if ES fails

    # Delete PDF file
    try:
        file_path = Path(doc.file_path)
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to delete file: {e}")
        # Continue with deletion even if file deletion fails

    # Delete from database
    pg_client.delete_document(document_id)

    logger.info(f"Document {document_id} deleted successfully")


@router.get("/{document_id}/download")
async def download_document(
    document_id: str, api_key: str = Depends(verify_api_key)
) -> FileResponse:
    """
    Download the original PDF document.

    Args:
        document_id: Document ID
        api_key: API key for authentication

    Returns:
        FileResponse: PDF file download

    Raises:
        HTTPException: If document not found or file missing
    """
    pg_client = get_postgres_client()

    # Get document
    doc = pg_client.get_document(document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Check if file exists
    file_path = Path(doc.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PDF file not found for document {document_id}",
        )

    # Return file
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=doc.filename,
    )
