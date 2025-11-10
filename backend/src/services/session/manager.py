"""Session manager for conversation sessions."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID

from ...models.session import ConversationSession

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages in-memory conversation sessions with timeout cleanup."""

    def __init__(self, timeout_minutes: int = 30):
        """
        Initialize session manager.

        Args:
            timeout_minutes: Session timeout in minutes
        """
        self.timeout_minutes = timeout_minutes
        self.sessions: Dict[UUID, ConversationSession] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    def create_session(self) -> ConversationSession:
        """
        Create a new conversation session.

        Returns:
            New ConversationSession instance
        """
        session = ConversationSession()
        self.sessions[session.session_id] = session
        logger.info(f"Created new session: {session.session_id}")
        return session

    def get_session(self, session_id: UUID) -> Optional[ConversationSession]:
        """
        Get an existing session by ID.

        Args:
            session_id: Session identifier

        Returns:
            ConversationSession if found, None otherwise
        """
        session = self.sessions.get(session_id)
        if session:
            # Update last activity timestamp
            session.last_activity = datetime.utcnow()
        return session

    def get_or_create_session(
        self,
        session_id: Optional[UUID] = None
    ) -> ConversationSession:
        """
        Get existing session or create a new one.

        Args:
            session_id: Optional session identifier

        Returns:
            ConversationSession instance
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
            logger.warning(
                f"Session {session_id} not found or expired, creating new session"
            )

        return self.create_session()

    def delete_session(self, session_id: UUID) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False

    def cleanup_expired_sessions(self) -> int:
        """
        Remove sessions that have exceeded the timeout.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        timeout_delta = timedelta(minutes=self.timeout_minutes)
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if now - session.last_activity > timeout_delta:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        return len(expired_sessions)

    async def start_cleanup_task(self) -> None:
        """Start background task for periodic session cleanup."""
        if self._cleanup_task is not None:
            logger.warning("Cleanup task already running")
            return

        async def cleanup_loop():
            """Periodic cleanup loop."""
            # Run cleanup every 5 minutes
            cleanup_interval = 300  # 5 minutes in seconds

            while True:
                try:
                    await asyncio.sleep(cleanup_interval)
                    self.cleanup_expired_sessions()
                except asyncio.CancelledError:
                    logger.info("Cleanup task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("Started session cleanup task")

    async def stop_cleanup_task(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Stopped session cleanup task")

    def get_stats(self) -> dict:
        """
        Get session manager statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "total_sessions": len(self.sessions),
            "timeout_minutes": self.timeout_minutes
        }
