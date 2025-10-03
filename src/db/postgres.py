"""
PostgreSQL database client for document metadata storage.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    DateTime,
    Enum as SQLEnum,
    Text,
    BigInteger
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from src.config import settings
from src.models.document import ProcessingStatus, DocumentCategory
from src.utils.logging import get_logger

logger = get_logger(__name__)

# SQLAlchemy Base
Base = declarative_base()


class Document(Base):
    """Document metadata model for PostgreSQL."""

    __tablename__ = "documents"

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)  # Storage filename (UUID-based)
    original_filename = Column(String(255), nullable=False)  # Original uploaded filename
    file_path = Column(String(512), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # Bytes
    category = Column(SQLEnum(DocumentCategory), nullable=False)
    machine_model = Column(String(100), nullable=True)
    processing_status = Column(SQLEnum(ProcessingStatus), nullable=False, default=ProcessingStatus.UPLOADED)
    total_pages = Column(Integer, nullable=True)
    upload_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    indexed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "document_id": self.id,
            "filename": self.original_filename,  # Return original filename for display
            "storage_filename": self.filename,  # Internal storage filename
            "file_path": self.file_path,
            "file_size": self.file_size,
            "category": self.category.value if self.category else None,
            "machine_model": self.machine_model,
            "processing_status": self.processing_status.value if self.processing_status else None,
            "total_pages": self.total_pages,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "indexed_at": self.indexed_at.isoformat() if self.indexed_at else None,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PostgreSQLClient:
    """PostgreSQL client with connection pooling."""

    def __init__(self):
        """Initialize PostgreSQL client."""
        self._engine = None
        self._session_factory = None
        self._initialize_engine()

    def _initialize_engine(self) -> None:
        """Create SQLAlchemy engine with connection pooling."""
        try:
            self._engine = create_engine(
                settings.database_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
                echo=False  # Set to True for SQL logging
            )

            self._session_factory = sessionmaker(bind=self._engine)

            logger.info(f"PostgreSQL engine initialized: {settings.database_url.split('@')[1]}")

        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL engine: {e}")
            raise

    def create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            Base.metadata.create_all(self._engine)
            logger.info("Database tables created/verified")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            Session: SQLAlchemy session

        Note: Caller is responsible for closing the session
        """
        return self._session_factory()

    def create_document(
        self,
        document_id: str,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        category: DocumentCategory,
        machine_model: Optional[str] = None
    ) -> Document:
        """
        Create a new document record.

        Args:
            document_id: Unique document identifier
            filename: Storage filename (UUID-based)
            original_filename: Original uploaded filename
            file_path: Path to stored PDF
            file_size: File size in bytes
            category: Document category
            machine_model: Optional machine model

        Returns:
            Document: Created document record
        """
        session = self.get_session()
        try:
            doc = Document(
                id=document_id,
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                category=category,
                machine_model=machine_model,
                processing_status=ProcessingStatus.UPLOADED
            )

            session.add(doc)
            session.commit()
            session.refresh(doc)

            logger.info(f"Created document record: {document_id}")
            return doc

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create document record: {e}")
            raise
        finally:
            session.close()

    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.

        Args:
            document_id: Document identifier

        Returns:
            Document: Document record or None if not found
        """
        session = self.get_session()
        try:
            doc = session.query(Document).filter(Document.id == document_id).first()
            return doc
        finally:
            session.close()

    def update_document_status(
        self,
        document_id: str,
        status: ProcessingStatus,
        error_message: Optional[str] = None,
        total_pages: Optional[int] = None,
        indexed_at: Optional[datetime] = None
    ) -> bool:
        """
        Update document processing status.

        Args:
            document_id: Document identifier
            status: New processing status
            error_message: Optional error message
            total_pages: Optional total page count
            indexed_at: Optional indexing timestamp

        Returns:
            bool: True if updated, False if document not found
        """
        session = self.get_session()
        try:
            doc = session.query(Document).filter(Document.id == document_id).first()

            if not doc:
                logger.warning(f"Document not found: {document_id}")
                return False

            doc.processing_status = status
            if error_message is not None:
                doc.error_message = error_message
            if total_pages is not None:
                doc.total_pages = total_pages
            if indexed_at is not None:
                doc.indexed_at = indexed_at

            session.commit()
            logger.info(f"Updated document {document_id} status to {status.value}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update document status: {e}")
            raise
        finally:
            session.close()

    def list_documents(
        self,
        status: Optional[ProcessingStatus] = None,
        category: Optional[DocumentCategory] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """
        List documents with optional filters.

        Args:
            status: Optional status filter
            category: Optional category filter
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            list: List of document records
        """
        session = self.get_session()
        try:
            query = session.query(Document)

            if status:
                query = query.filter(Document.processing_status == status)
            if category:
                query = query.filter(Document.category == category)

            query = query.order_by(Document.upload_date.desc())
            query = query.limit(limit).offset(offset)

            docs = query.all()
            return docs

        finally:
            session.close()

    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document record.

        Args:
            document_id: Document identifier

        Returns:
            bool: True if deleted, False if not found
        """
        session = self.get_session()
        try:
            doc = session.query(Document).filter(Document.id == document_id).first()

            if not doc:
                logger.warning(f"Document not found: {document_id}")
                return False

            session.delete(doc)
            session.commit()
            logger.info(f"Deleted document record: {document_id}")
            return True

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete document: {e}")
            raise
        finally:
            session.close()

    def count_documents(
        self,
        status: Optional[ProcessingStatus] = None,
        category: Optional[DocumentCategory] = None
    ) -> int:
        """
        Count documents with optional filters.

        Args:
            status: Optional status filter
            category: Optional category filter

        Returns:
            int: Document count
        """
        session = self.get_session()
        try:
            query = session.query(Document)

            if status:
                query = query.filter(Document.processing_status == status)
            if category:
                query = query.filter(Document.category == category)

            count = query.count()
            return count

        finally:
            session.close()


# Global PostgreSQL client instance
_postgres_client: Optional[PostgreSQLClient] = None


def get_postgres_client() -> PostgreSQLClient:
    """
    Get the global PostgreSQL client instance (singleton pattern).

    Returns:
        PostgreSQLClient: The PostgreSQL client
    """
    global _postgres_client
    if _postgres_client is None:
        _postgres_client = PostgreSQLClient()
    return _postgres_client
