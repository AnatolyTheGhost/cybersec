from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RepositoryFile:
    relative_path: str
    content: str


class RepositoryReader:
    """Collect repository files while skipping obvious technical directories."""

    _IGNORED_DIRECTORIES = {".git", "__pycache__", "node_modules", ".venv", ".pytest_cache", ".mypy_cache"}

    def read(self, workspace_path: str | Path) -> list[RepositoryFile]:
        root = Path(workspace_path).resolve()

        if not root.exists():
            raise FileNotFoundError(f"Workspace does not exist: {root}")

        if root.is_file():
            try:
                content = root.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return []

            return [
                RepositoryFile(
                    relative_path=root.name,
                    content=content,
                )
            ]

        files: list[RepositoryFile] = []

        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue

            try:
                relative_path = path.relative_to(root).as_posix()
            except ValueError:
                continue

            if self._is_ignored_path(relative_path):
                continue

            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            files.append(
                RepositoryFile(
                    relative_path=relative_path,
                    content=content,
                )
            )

        return files

def _is_ignored_path(self, relative_path: str) -> bool:
    parts = [part for part in relative_path.split("/") if part]
    return any(part in self._IGNORED_DIRECTORIES for part in parts)
