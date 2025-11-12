"""Session management endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ...models.session import SessionResponse
from ...services.session.manager import SessionManager
from ..dependencies import get_session_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    session_manager: SessionManager = Depends(get_session_manager)
) -> SessionResponse:
    """
    Get session information.

    """
    session = session_manager.get_session(session_id)

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found or expired"
        )

    return SessionResponse(
        session_id=session.session_id,
        message_count=len(session.messages),
        created_at=session.created_at,
        last_activity=session.last_activity
    )


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: UUID,
    session_manager: SessionManager = Depends(get_session_manager)
) -> dict:
    """
    Delete a session.


    """
    deleted = session_manager.delete_session(session_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"Session {session_id} not found"
        )

    logger.info(f"Deleted session {session_id}")

    return {"message": f"Session {session_id} deleted successfully"}
