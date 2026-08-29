from __future__ import annotations

import hashlib
import os
from typing import Callable, Iterable

from .adapters import MutationAdapter
from .backend_client import BackendClient
from .events import MutationEvent
from .registry import AdapterRegistry


def _derive_workspace_id(repository_path: str) -> str:
    abs_path = os.path.abspath(repository_path)
    digest = hashlib.sha1(abs_path.encode("utf-8")).hexdigest()
    return f"repo-{digest}"


class MutationsReceiver:
    """Central ingestion point that validates and forwards mutation events."""

    def __init__(
        self,
        adapters: Iterable[MutationAdapter] | None = None,
        backend_client: BackendClient | None = None,
    ) -> None:
        self._registry = AdapterRegistry()
        self._consumers: list[Callable[[MutationEvent], None]] = []
        self._started = False
        self._backend_client = backend_client
        self._file_hashes: dict[str, str] = {}
        self._workspace_id: str | None = None
        self._workspace_path: str | None = None

        if adapters:
            for adapter in adapters:
                self.register_adapter(adapter)

    @property
    def started(self) -> bool:
        return self._started

    def register_adapter(self, adapter: MutationAdapter) -> None:
        self._registry.register(adapter)

    def add_consumer(self, consumer: Callable[[MutationEvent], None]) -> None:
        self._consumers.append(consumer)

    def set_backend_client(self, backend_client: BackendClient | None) -> None:
        self._backend_client = backend_client

    def connect_backend(self, workspace_id: str, workspace_path: str, goals: list[str] | None = None) -> dict[str, object] | None:
        if self._backend_client is None:
            return None
        self._backend_client.health()
        if goals is None:
            goals = ["security"]
        self._workspace_id = workspace_id
        self._workspace_path = workspace_path
        return self._backend_client.start_analysis(workspace_id, workspace_path, goals)

    def submit_workspace_mutations(self, workspace_id: str, mutations: list[MutationEvent]) -> dict[str, object] | None:
        if self._backend_client is None:
            return None
        payload = [mutation.to_dict() for mutation in mutations]
        return self._backend_client.submit_mutations(workspace_id, payload)

    def _calculate_sha256(self, file_path: str) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def scan_project(self, workspace_path: str | None = None) -> None:
        if workspace_path is not None:
            self._workspace_path = workspace_path
        if not self._workspace_path:
            raise ValueError("Workspace path not set")

        self._file_hashes.clear()
        abs_workspace = os.path.abspath(self._workspace_path)
        for root, dirs, files in os.walk(abs_workspace):
            # Skip common ignored directories
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", ".pytest_cache", "__pycache__", ".vscode"}]
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    self._file_hashes[file_path] = self._calculate_sha256(file_path)
                except (OSError, PermissionError):
                    # Skip files we cannot read
                    pass

    def start(self) -> None:
        for adapter in self._registry.all():
            adapter.initialize()
            adapter.start(self._handle_event)
        self._started = True

    def stop(self) -> None:
        for adapter in self._registry.all():
            adapter.stop()
        self._started = False

    def handle_event(self, event: MutationEvent) -> bool:
        if not self.validate_event(event):
            return False

        # Intercept file save events for Mutations Tracking Mechanism
        if event.event_type == "FileSaved" and event.file_path:
            abs_path = os.path.abspath(event.file_path)
            if os.path.exists(abs_path):
                try:
                    new_hash = self._calculate_sha256(abs_path)
                    cached_hash = self._file_hashes.get(abs_path)
                    if cached_hash != new_hash:
                        self._file_hashes[abs_path] = new_hash
                        # Read the file content and attach it to payload
                        try:
                            with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                                event.payload["content"] = f.read()
                        except (OSError, PermissionError):
                            pass

                        # Determine workspace_id
                        workspace_id = self._workspace_id
                        if not workspace_id and self._workspace_path:
                            workspace_id = _derive_workspace_id(self._workspace_path)
                        
                        if workspace_id:
                            self.submit_workspace_mutations(workspace_id, [event])
                except (OSError, PermissionError):
                    pass

        self._forward_to_consumers(event)
        return True

    def validate_event(self, event: MutationEvent) -> bool:
        if not event.event_type.strip():
            return False
        if event.timestamp is None:
            return False
        if not event.session_id.strip():
            return False
        if not event.source_adapter.strip():
            return False
        if not isinstance(event.payload, dict):
            return False
        return True

    def _handle_event(self, event: MutationEvent) -> None:
        self.handle_event(event)

    def _forward_to_consumers(self, event: MutationEvent) -> None:
        for consumer in self._consumers:
            consumer(event)
