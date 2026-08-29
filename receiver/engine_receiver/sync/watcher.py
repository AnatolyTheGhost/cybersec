from __future__ import annotations

from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from engine_receiver.repository_reader import RepositoryReader


class _WatchdogHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[str, str], None], root: Path) -> None:
        super().__init__()
        self.callback = callback
        self.root = root
        self.reader = RepositoryReader()

    def _process(self, event: FileSystemEvent, event_type: str) -> None:
        if event.is_directory:
            return

        try:
            rel_path = Path(event.src_path).relative_to(self.root).as_posix()
        except ValueError:
            return

        if self.reader._is_ignored_path(rel_path):
            return

        self.callback(event_type, rel_path)

    def on_created(self, event: FileSystemEvent) -> None:
        self._process(event, "created")

    def on_modified(self, event: FileSystemEvent) -> None:
        self._process(event, "modified")

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._process(event, "deleted")


class FileWatcher:
    """Emits file system events."""
    def __init__(self, workspace_path: str, on_event: Callable[[str, str], None]) -> None:
        self.workspace_path = Path(workspace_path).resolve()
        self.on_event = on_event
        self.observer: Observer | None = None

    def start(self) -> None:
        if self.observer is not None:
            return
            
        handler = _WatchdogHandler(self.on_event, self.workspace_path)
        self.observer = Observer()
        self.observer.schedule(handler, str(self.workspace_path), recursive=True)
        self.observer.start()

    def stop(self) -> None:
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
