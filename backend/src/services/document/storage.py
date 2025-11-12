"""Document storage and registry service."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID

from ...models.document import LegalDocument, ProcessingStatus

logger = logging.getLogger(__name__)


class DocumentStorage:
    """Manages document metadata and file storage."""

    def __init__(self, upload_dir: Path):
        """
        Initialize document storage.

        Args:
            upload_dir: Directory for storing uploaded files
        """
        self.upload_dir = upload_dir
        self.documents: Dict[UUID, LegalDocument] = {}

        # Ensure upload directory exists
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Document storage initialized at {upload_dir}")

    def create_document(
        self,
        title: str,
        file_path: str,
        file_size_bytes: int
    ) -> LegalDocument:
        """
        Create a new document entry.

        """
        document = LegalDocument(
            title=title,
            file_path=file_path,
            file_size_bytes=file_size_bytes,
            processing_status=ProcessingStatus.PENDING
        )

        self.documents[document.document_id] = document
        logger.info(f"Created document {document.document_id}: {title}")

        return document

    def get_document(self, document_id: UUID) -> Optional[LegalDocument]:
        """
        Get a document by ID.

        """
        return self.documents.get(document_id)

    def list_documents(self) -> List[LegalDocument]:
        """
        List all documents.

        """
        return list(self.documents.values())

    def update_document_status(
        self,
        document_id: UUID,
        status: ProcessingStatus,
        error_message: Optional[str] = None,
        total_chunks: int = 0
    ) -> None:
        """
        Update document processing status.

        Args:
            document_id: Document identifier
            status: New processing status
            error_message: Optional error message if processing failed
            total_chunks: Total number of chunks created
        """
        document = self.documents.get(document_id)
        if not document:
            logger.warning(f"Document {document_id} not found for status update")
            return

        document.processing_status = status

        if status == ProcessingStatus.COMPLETED:
            document.processed_at = datetime.utcnow()
            document.total_chunks = total_chunks
            logger.info(
                f"Document {document_id} processing completed. "
                f"Created {total_chunks} chunks."
            )

        elif status == ProcessingStatus.FAILED:
            document.error_message = error_message
            logger.error(f"Document {document_id} processing failed: {error_message}")

        elif status == ProcessingStatus.PROCESSING:
            logger.info(f"Document {document_id} processing started")

    def delete_document(self, document_id: UUID) -> bool:
        """
        Delete a document and its file.


        """
        document = self.documents.get(document_id)
        if not document:
            return False

        # Delete the file
        try:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete file {document.file_path}: {e}")

        # Remove from registry
        del self.documents[document_id]
        logger.info(f"Deleted document {document_id}")

        return True

    def save_uploaded_file(self, file_content: bytes, filename: str) -> Path:
        """
        Save uploaded file to disk.


        """
        try:
            # Generate unique filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"{timestamp}_{filename}"
            file_path = self.upload_dir / safe_filename

            # Write file
            with open(file_path, "wb") as f:
                f.write(file_content)

            logger.info(f"Saved uploaded file: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to save uploaded file {filename}: {e}")
            raise
