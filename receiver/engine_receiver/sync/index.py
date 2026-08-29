from __future__ import annotations

from engine_receiver.repository_reader import RepositoryFile
from .hashing import compute_hash


class FileIndex:
    """Stores path -> hash mappings."""

    def __init__(self) -> None:
        self._hashes: dict[str, str] = {}

    def build(self, files: list[RepositoryFile]) -> None:
        self._hashes.clear()
        for file in files:
            self._hashes[file.relative_path] = compute_hash(file.content)

    def update(self, path: str, hash_val: str) -> None:
        self._hashes[path] = hash_val

    def remove(self, path: str) -> None:
        self._hashes.pop(path, None)

    def get_hash(self, path: str) -> str | None:
        return self._hashes.get(path)
