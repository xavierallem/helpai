"""Shared pytest fixtures for backend tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api import dependencies
from src.api.main import app
from src.services.session.manager import SessionManager


@pytest.fixture
def session_manager():
    """Return a fresh SessionManager for each test."""
    return SessionManager(timeout_minutes=30)


@pytest.fixture
def mock_chromadb_client():
    """Return a mocked ChromaDBClient."""
    client = MagicMock()
    client.get_collection_stats.return_value = {
        "total_chunks": 42,
        "collection_name": "legal_documents",
        "embedding_model": "all-MiniLM-L6-v2",
    }
    return client


@pytest.fixture
def api_client(mock_chromadb_client, session_manager):
    """Return a FastAPI TestClient with all external services mocked.

    Patches ChromaDBClient, DocumentStorage, and SessionManager in the
    lifespan so no real DB connections or model downloads happen — safe
    for GitHub Actions CI.
    """
    mock_storage = MagicMock()

    with (
        patch("src.api.main.ChromaDBClient", return_value=mock_chromadb_client),
        patch("src.api.main.DocumentStorage", return_value=mock_storage),
        patch("src.api.main.SessionManager", return_value=session_manager),
        patch.object(session_manager, "start_cleanup_task", new=AsyncMock()),
    ):
        dependencies.chromadb_client = mock_chromadb_client
        dependencies.session_manager = session_manager
        dependencies.document_storage = mock_storage

        with TestClient(app) as client:
            yield client
