"""Integration tests for the sessions endpoints."""

from uuid import uuid4


class TestSessionsEndpoints:
    def test_get_nonexistent_session_returns_404(self, api_client):
        response = api_client.get(f"/api/sessions/{uuid4()}")
        assert response.status_code == 404

    def test_get_existing_session(self, api_client, session_manager):
        session = session_manager.create_session()
        response = api_client.get(f"/api/sessions/{session.session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session.session_id)
        assert data["message_count"] == 0

    def test_get_session_with_messages(self, api_client, session_manager):
        session = session_manager.create_session()
        session.add_message(role="user", content="Hello")
        session.add_message(role="assistant", content="Hi")
        response = api_client.get(f"/api/sessions/{session.session_id}")
        assert response.status_code == 200
        assert response.json()["message_count"] == 2

    def test_delete_existing_session(self, api_client, session_manager):
        session = session_manager.create_session()
        response = api_client.delete(f"/api/sessions/{session.session_id}")
        assert response.status_code == 200
        assert "deleted" in response.json()["message"].lower()

    def test_delete_nonexistent_session_returns_404(self, api_client):
        response = api_client.delete(f"/api/sessions/{uuid4()}")
        assert response.status_code == 404

    def test_get_session_invalid_uuid_returns_422(self, api_client):
        response = api_client.get("/api/sessions/not-a-uuid")
        assert response.status_code == 422

    def test_session_response_has_required_fields(self, api_client, session_manager):
        session = session_manager.create_session()
        data = api_client.get(f"/api/sessions/{session.session_id}").json()
        for field in ("session_id", "message_count", "created_at", "last_activity"):
            assert field in data
