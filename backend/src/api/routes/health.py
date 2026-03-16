"""Health check endpoint."""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends

from ...services.session.manager import SessionManager
from ...services.vectordb.client import ChromaDBClient
from ..dependencies import get_chromadb_client, get_session_manager

router = APIRouter()


@router.get("/health")
async def health_check(
    chromadb_client: ChromaDBClient = Depends(get_chromadb_client),
    session_manager: SessionManager = Depends(get_session_manager),
) -> dict[str, Any]:
    """
    Health check endpoint.

    """
    try:
        # Get ChromaDB stats
        chromadb_stats = chromadb_client.get_collection_stats()

        # Get session manager stats
        session_stats = session_manager.get_stats()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                "chromadb": {
                    "status": "operational",
                    "total_chunks": chromadb_stats["total_chunks"],
                    "collection_name": chromadb_stats["collection_name"],
                    "embedding_model": chromadb_stats["embedding_model"],
                },
                "sessions": {
                    "status": "operational",
                    "active_sessions": session_stats["total_sessions"],
                    "timeout_minutes": session_stats["timeout_minutes"],
                },
            },
        }

    except Exception as e:
        return {"status": "unhealthy", "timestamp": datetime.utcnow().isoformat(), "error": str(e)}
