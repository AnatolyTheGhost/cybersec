from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ScanSession:
    """In-memory session holding scan state for the receiver pipeline."""

    workspace_path: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pack: str | None = None
    status: str = "running"
    findings: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None

    def finish(self, findings: list[dict[str, Any]], status: str = "completed", error: str | None = None) -> None:
        self.findings = findings
        self.status = status
        self.error = error

    @property
    def finding_count(self) -> int:
        return len(self.findings)
