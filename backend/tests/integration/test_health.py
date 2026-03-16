"""Integration tests for the health endpoint."""

from unittest.mock import MagicMock

import pytest


class TestHealthEndpoint:
    def test_health_returns_200(self, api_client):
        response = api_client.get("/health")
        assert response.status_code == 200

    def test_health_status_healthy(self, api_client):
        data = api_client.get("/health").json()
        assert data["status"] == "healthy"

    def test_health_has_timestamp(self, api_client):
        data = api_client.get("/health").json()
        assert "timestamp" in data

    def test_health_components_present(self, api_client):
        data = api_client.get("/health").json()
        assert "components" in data
        assert "chromadb" in data["components"]
        assert "sessions" in data["components"]

    def test_health_chromadb_stats(self, api_client):
        data = api_client.get("/health").json()
        chromadb = data["components"]["chromadb"]
        assert chromadb["status"] == "operational"
        assert chromadb["total_chunks"] == 42
        assert chromadb["collection_name"] == "legal_documents"

    def test_health_sessions_stats(self, api_client):
        data = api_client.get("/health").json()
        sessions = data["components"]["sessions"]
        assert sessions["status"] == "operational"
        assert "active_sessions" in sessions

    def test_health_degraded_on_chromadb_error(self, session_manager):
        from unittest.mock import AsyncMock, patch
        from fastapi.testclient import TestClient
        from src.api import dependencies
        from src.api.main import app

        broken_client = MagicMock()
        broken_client.get_collection_stats.side_effect = Exception("DB down")

        with (
            patch("src.api.main.ChromaDBClient", return_value=broken_client),
            patch("src.api.main.DocumentStorage"),
            patch("src.api.main.SessionManager", return_value=session_manager),
            patch.object(session_manager, "start_cleanup_task", new=AsyncMock()),
        ):
            dependencies.chromadb_client = broken_client
            dependencies.session_manager = session_manager
            dependencies.document_storage = MagicMock()

            with TestClient(app) as client:
                response = client.get("/health")

        # Should still return a response (degraded), not 500
        assert response.status_code == 200
        assert response.json()["status"] != "healthy"
