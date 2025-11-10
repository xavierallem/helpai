"""Document processing orchestrator."""

import logging
from pathlib import Path
from uuid import UUID

from ...models.document import LegalDocument, ProcessingStatus
from ..vectordb.client import ChromaDBClient
from .pdf_extractor import PDFExtractor
from .storage import DocumentStorage
from .text_chunker import TextChunker

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates document processing pipeline."""

    def __init__(
        self,
        storage: DocumentStorage,
        vectordb_client: ChromaDBClient,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize document processor.

        Args:
            storage: Document storage instance
            vectordb_client: ChromaDB client instance
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.storage = storage
        self.vectordb_client = vectordb_client
        self.pdf_extractor = PDFExtractor()
        self.text_chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    async def process_document(self, document_id: UUID) -> None:
        """
        Process a document: extract text, chunk, and store in vector DB.

        Args:
            document_id: Document to process

        Raises:
            Exception: If processing fails
        """
        document = self.storage.get_document(document_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        try:
            # Update status to processing
            self.storage.update_document_status(
                document_id,
                ProcessingStatus.PROCESSING
            )

            logger.info(f"Starting processing for document {document_id}")

            # Step 1: Validate PDF
            file_path = Path(document.file_path)
            if not self.pdf_extractor.validate_pdf(file_path):
                raise ValueError("Invalid or corrupted PDF file")

            # Step 2: Extract text from PDF
            pages_text = self.pdf_extractor.extract_text_from_pdf(file_path)

            if not pages_text:
                raise ValueError("No text could be extracted from PDF")

            # Step 3: Chunk the text
            chunks = self.text_chunker.chunk_document(document_id, pages_text)

            if not chunks:
                raise ValueError("No chunks created from document")

            # Step 4: Store chunks in vector database
            self.vectordb_client.add_chunks(chunks)

            # Step 5: Update document status to completed
            self.storage.update_document_status(
                document_id,
                ProcessingStatus.COMPLETED,
                total_chunks=len(chunks)
            )

            logger.info(
                f"Successfully processed document {document_id}. "
                f"Created {len(chunks)} chunks from {len(pages_text)} pages."
            )

        except Exception as e:
            # Update status to failed
            error_msg = str(e)
            self.storage.update_document_status(
                document_id,
                ProcessingStatus.FAILED,
                error_message=error_msg
            )

            logger.error(f"Failed to process document {document_id}: {error_msg}")
            raise

    async def upload_and_process_document(
        self,
        title: str,
        file_content: bytes,
        filename: str
    ) -> LegalDocument:
        """
        Upload and process a document.

        Args:
            title: Document title
            file_content: File content as bytes
            filename: Original filename

        Returns:
            Created LegalDocument

        Raises:
            Exception: If upload or processing fails
        """
        try:
            # Validate file extension
            if not filename.lower().endswith('.pdf'):
                raise ValueError("Only PDF files are supported")

            # Save uploaded file
            file_path = self.storage.save_uploaded_file(file_content, filename)

            # Create document entry
            document = self.storage.create_document(
                title=title,
                file_path=str(file_path),
                file_size_bytes=len(file_content)
            )

            # Process the document
            await self.process_document(document.document_id)

            return document

        except Exception as e:
            logger.error(f"Failed to upload and process document: {e}")
            raise

    async def delete_document(self, document_id: UUID) -> bool:
        """
        Delete a document and its chunks from vector DB.

        Args:
            document_id: Document to delete

        Returns:
            True if deleted, False if not found
        """
        try:
            # Delete chunks from vector database
            self.vectordb_client.delete_document_chunks(str(document_id))

            # Delete document from storage
            deleted = self.storage.delete_document(document_id)

            if deleted:
                logger.info(f"Deleted document {document_id} and all its chunks")

            return deleted

        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
