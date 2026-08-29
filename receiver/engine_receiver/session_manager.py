from __future__ import annotations

from .session import ScanSession


class SessionManager:
    """Creates and finalizes in-memory scan sessions."""

    def create(self, workspace_path: str, pack: str | None = None) -> ScanSession:
        return ScanSession(workspace_path=workspace_path, pack=pack)

    def finish(self, session: ScanSession, findings: list[dict], status: str = "completed", error: str | None = None) -> ScanSession:
        session.finish(findings=findings, status=status, error=error)
        return session
