"""FastAPI dependencies."""

from ..services.session.manager import SessionManager
from ..services.vectordb.client import ChromaDBClient
from ..services.document.storage import DocumentStorage

# Global instances (set by main.py on startup)
chromadb_client: ChromaDBClient = None
session_manager: SessionManager = None
document_storage: DocumentStorage = None


def get_chromadb_client() -> ChromaDBClient:
    """
    Dependency to get ChromaDB client.

    Returns:
        ChromaDBClient instance

    Raises:
        RuntimeError: If client is not initialized
    """
    if chromadb_client is None:
        raise RuntimeError("ChromaDB client not initialized")
    return chromadb_client


def get_session_manager() -> SessionManager:
    """
    Dependency to get Session Manager.

    Returns:
        SessionManager instance

    Raises:
        RuntimeError: If session manager is not initialized
    """
    if session_manager is None:
        raise RuntimeError("Session manager not initialized")
    return session_manager


def get_document_storage() -> DocumentStorage:
    """
    Dependency to get Document Storage.

    Returns:
        DocumentStorage instance

    Raises:
        RuntimeError: If document storage is not initialized
    """
    if document_storage is None:
        raise RuntimeError("Document storage not initialized")
    return document_storage
