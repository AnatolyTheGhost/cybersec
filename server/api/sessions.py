"""
Sessions API Endpoint Module.

Provides FastAPI endpoints for user analysis session management.

Responsibility:
- HTTP request validation for session lifecycle (start, end, query).
- Response serialization.
- Calling SessionService.

No business logic allowed here.

TODO:
- Integrate session authorization tokens and workspace access controls.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from models.schemas import SessionEndRequest, SessionResponse, SessionStartRequest
from services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])

_session_service = SessionService()


def get_session_service() -> SessionService:
    """Dependency injector for SessionService."""
    return _session_service


@router.post("/start", response_model=SessionResponse)
def start_session(
    request: SessionStartRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """
    Start a new workspace analysis session.

    TODO: Pass user token to service for permission check.
    """
    return service.start_session(
        workspace_id=request.workspace_id,
        workspace_path=request.workspace_path,
        metadata=request.metadata,
    )


@router.post("/end", response_model=SessionResponse)
def end_session(
    request: SessionEndRequest,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """
    End an active session.

    TODO: Ensure background analysis cleanup finishes on session termination.
    """
    try:
        return service.end_session(request.session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    service: SessionService = Depends(get_session_service),
) -> SessionResponse:
    """
    Get active session status by session ID.

    TODO: Return expanded workspace context summary.
    """
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session with ID {session_id} not found")
    return session
