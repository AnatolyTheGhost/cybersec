from __future__ import annotations

import logging
from pathlib import Path

from engine_receiver.transport import Transport
from .hashing import compute_hash
from .index import FileIndex
from .watcher import FileWatcher

logger = logging.getLogger(__name__)


class SyncManager:
    """Orchestrates file change detection and synchronization."""

    def __init__(self, workspace_path: str, session_id: str, transport: Transport, index: FileIndex) -> None:
        self.workspace_path = Path(workspace_path).resolve()
        self.session_id = session_id
        self.transport = transport
        self.index = index
        self.watcher = FileWatcher(str(self.workspace_path), self._on_file_event)

    def start(self) -> None:
        self.watcher.start()

    def stop(self) -> None:
        self.watcher.stop()

    def _on_file_event(self, event_type: str, rel_path: str) -> None:
        full_path = self.workspace_path / rel_path
        
        content = ""
        new_hash = ""
        
        if event_type in ("created", "modified"):
            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
                new_hash = compute_hash(content)
            except OSError:
                return
            
            old_hash = self.index.get_hash(rel_path)
            if old_hash == new_hash:
                return
            
            self.index.update(rel_path, new_hash)
        elif event_type == "deleted":
            old_hash = self.index.get_hash(rel_path)
            if old_hash is None:
                return
            
            self.index.remove(rel_path)
        else:
            return

        try:
            self.transport.send_file_changes(self.session_id, [{
                "path": rel_path,
                "change_type": event_type,
                "content": content
            }])
        except Exception:
            pass # Or log it if a logger is configured
