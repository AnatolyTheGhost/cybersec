from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable

from .events import MutationEvent


class MutationAdapter(ABC):
    """Abstract interface for adapters that emit normalized mutation events."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._started = False
        self._initialized = False
        self._event_sink: Callable[[MutationEvent], None] | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def started(self) -> bool:
        return self._started

    @property
    def initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> None:
        self._initialized = True

    def start(self, event_sink: Callable[[MutationEvent], None]) -> None:
        self._event_sink = event_sink
        self._started = True

    def stop(self) -> None:
        self._started = False
        self._event_sink = None

    def emit(self, event: MutationEvent) -> None:
        if not self._started or self._event_sink is None:
            return
        self._event_sink(event)

    @abstractmethod
    def emit_test_event(
        self,
        event_type: str,
        *,
        file_path: str | None = None,
        payload: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        session_id: str | None = None,
    ) -> None:
        """Emit a normalized event for testing or placeholder integration."""


class VSCodeAdapter(MutationAdapter):
    """Placeholder adapter for editor-driven events."""

    def __init__(self, name: str = "vscode") -> None:
        super().__init__(name)

    def emit_test_event(
        self,
        event_type: str,
        *,
        file_path: str | None = None,
        payload: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        session_id: str | None = None,
    ) -> None:
        self.emit(
            MutationEvent(
                event_type=event_type,
                timestamp=timestamp or datetime.now(timezone.utc),
                session_id=session_id or "demo-session",
                source_adapter=self.name,
                file_path=file_path,
                payload=payload or {"source": "vscode"},
            )
        )


class FileWatcherAdapter(MutationAdapter):
    """Placeholder adapter for file-system-driven events."""

    def __init__(self, name: str = "filewatcher") -> None:
        super().__init__(name)

    def emit_test_event(
        self,
        event_type: str,
        *,
        file_path: str | None = None,
        payload: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        session_id: str | None = None,
    ) -> None:
        self.emit(
            MutationEvent(
                event_type=event_type,
                timestamp=timestamp or datetime.now(timezone.utc),
                session_id=session_id or "demo-session",
                source_adapter=self.name,
                file_path=file_path,
                payload=payload or {"source": "filewatcher"},
            )
        )


class ClaudeCodeAdapter(MutationAdapter):
    """Placeholder adapter for tool-driven events."""

    def __init__(self, name: str = "claude") -> None:
        super().__init__(name)

    def emit_test_event(
        self,
        event_type: str,
        *,
        file_path: str | None = None,
        payload: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
        session_id: str | None = None,
    ) -> None:
        self.emit(
            MutationEvent(
                event_type=event_type,
                timestamp=timestamp or datetime.now(timezone.utc),
                session_id=session_id or "demo-session",
                source_adapter=self.name,
                file_path=file_path,
                payload=payload or {"source": "claude"},
            )
        )
