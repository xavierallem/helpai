"""Unit tests for SessionManager."""

from datetime import datetime, timedelta
from uuid import uuid4

from src.services.session.manager import SessionManager


class TestSessionManager:
    def test_create_session(self, session_manager):
        session = session_manager.create_session()
        assert session.session_id is not None
        assert len(session.messages) == 0

    def test_get_existing_session(self, session_manager):
        session = session_manager.create_session()
        retrieved = session_manager.get_session(session.session_id)
        assert retrieved is not None
        assert retrieved.session_id == session.session_id

    def test_get_nonexistent_session_returns_none(self, session_manager):
        assert session_manager.get_session(uuid4()) is None

    def test_get_or_create_with_existing_id(self, session_manager):
        session = session_manager.create_session()
        retrieved = session_manager.get_or_create_session(session.session_id)
        assert retrieved.session_id == session.session_id

    def test_get_or_create_with_none_creates_new(self, session_manager):
        session = session_manager.get_or_create_session(None)
        assert session is not None
        assert session_manager.get_session(session.session_id) is not None

    def test_get_or_create_with_unknown_id_creates_new(self, session_manager):
        new_session = session_manager.get_or_create_session(uuid4())
        assert new_session is not None

    def test_delete_existing_session(self, session_manager):
        session = session_manager.create_session()
        result = session_manager.delete_session(session.session_id)
        assert result is True
        assert session_manager.get_session(session.session_id) is None

    def test_delete_nonexistent_session_returns_false(self, session_manager):
        assert session_manager.delete_session(uuid4()) is False

    def test_get_stats(self, session_manager):
        session_manager.create_session()
        session_manager.create_session()
        stats = session_manager.get_stats()
        assert stats["total_sessions"] == 2
        assert stats["timeout_minutes"] == 30

    def test_cleanup_expired_sessions(self):
        manager = SessionManager(timeout_minutes=1)
        session = manager.create_session()

        # Manually expire the session
        session.last_activity = datetime.utcnow() - timedelta(minutes=2)

        removed = manager.cleanup_expired_sessions()
        assert removed == 1
        assert manager.get_session(session.session_id) is None

    def test_cleanup_does_not_remove_active_sessions(self, session_manager):
        session_manager.create_session()
        removed = session_manager.cleanup_expired_sessions()
        assert removed == 0
        assert session_manager.get_stats()["total_sessions"] == 1
