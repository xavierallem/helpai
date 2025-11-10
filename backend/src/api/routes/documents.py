"""Document management endpoints."""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ...models.document import DocumentResponse
from ...services.document.processor import DocumentProcessor
from ...services.document.storage import DocumentStorage
from ...services.vectordb.client import ChromaDBClient
from ..dependencies import get_chromadb_client, get_document_storage

logger = logging.getLogger(__name__)

router = APIRouter()


def get_document_processor(
    storage: DocumentStorage = Depends(get_document_storage),
    chromadb_client: ChromaDBClient = Depends(get_chromadb_client)
) -> DocumentProcessor:
    """
    Dependency to get document processor.

    Args:
        storage: Document storage instance
        chromadb_client: ChromaDB client instance

    Returns:
        DocumentProcessor instance
    """
    return DocumentProcessor(
        storage=storage,
        vectordb_client=chromadb_client,
        chunk_size=1000,
        chunk_overlap=200
    )


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    processor: DocumentProcessor = Depends(get_document_processor)
) -> DocumentResponse:
    """
    Upload and process a legal document.

    Args:
        file: PDF file to upload
        title: Document title
        processor: Document processor instance

    Returns:
        Document information

    Raises:
        HTTPException: If upload or processing fails
    """
    try:
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are supported"
            )

        # Read file content
        file_content = await file.read()

        # Check file size (from settings, default 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB"
            )

        logger.info(f"Uploading document: {title} ({file.filename})")

        # Upload and process document
        document = await processor.upload_and_process_document(
            title=title,
            file_content=file_content,
            filename=file.filename
        )

        return DocumentResponse(
            document_id=document.document_id,
            title=document.title,
            processing_status=document.processing_status,
            uploaded_at=document.uploaded_at,
            processed_at=document.processed_at,
            total_chunks=document.total_chunks,
            file_size_bytes=document.file_size_bytes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload document: {str(e)}"
        )


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    storage: DocumentStorage = Depends(get_document_storage)
) -> List[DocumentResponse]:
    """
    List all documents.

    Args:
        storage: Document storage instance

    Returns:
        List of all documents
    """
    try:
        documents = storage.list_documents()

        return [
            DocumentResponse(
                document_id=doc.document_id,
                title=doc.title,
                processing_status=doc.processing_status,
                uploaded_at=doc.uploaded_at,
                processed_at=doc.processed_at,
                total_chunks=doc.total_chunks,
                file_size_bytes=doc.file_size_bytes
            )
            for doc in documents
        ]

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    storage: DocumentStorage = Depends(get_document_storage)
) -> DocumentResponse:
    """
    Get document information.

    Args:
        document_id: Document identifier
        storage: Document storage instance

    Returns:
        Document information

    Raises:
        HTTPException: If document not found
    """
    document = storage.get_document(document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found"
        )

    return DocumentResponse(
        document_id=document.document_id,
        title=document.title,
        processing_status=document.processing_status,
        uploaded_at=document.uploaded_at,
        processed_at=document.processed_at,
        total_chunks=document.total_chunks,
        file_size_bytes=document.file_size_bytes
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    processor: DocumentProcessor = Depends(get_document_processor)
) -> dict:
    """
    Delete a document and its chunks.

    Args:
        document_id: Document identifier
        processor: Document processor instance

    Returns:
        Success message

    Raises:
        HTTPException: If document not found or deletion fails
    """
    try:
        deleted = await processor.delete_document(document_id)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )

        logger.info(f"Deleted document {document_id}")

        return {"message": f"Document {document_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )
