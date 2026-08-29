import threading
from typing import Dict, Iterable, List, Optional
from .models import Artifact
from .graph import DependencyGraph


class ArtifactRegistry:
    """
    Centralized registry for all addressable artifacts.
    Provides O(1) lookups by ID and stable_key, and maintains indices by file and kind.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._by_id: Dict[str, Artifact] = {}
        self._by_stable_key: Dict[str, Artifact] = {}
        self._by_file: Dict[str, set[str]] = {}
        self._by_kind: Dict[str, set[str]] = {}
        self.graph = DependencyGraph()

    def register(self, artifact: Artifact) -> None:
        """Register a new artifact."""
        with self._lock:
            if artifact.id in self._by_id:
                raise ValueError(f"Artifact with id {artifact.id} already exists.")
            if artifact.stable_key in self._by_stable_key:
                raise ValueError(f"Artifact with stable_key {artifact.stable_key} already exists.")

            self._by_id[artifact.id] = artifact
            self._by_stable_key[artifact.stable_key] = artifact
            self._by_file.setdefault(artifact.file, set()).add(artifact.id)
            self._by_kind.setdefault(artifact.kind, set()).add(artifact.id)
            self.graph.add_node(artifact.id)

    def update(self, artifact: Artifact) -> None:
        """Update an existing artifact."""
        with self._lock:
            if artifact.id not in self._by_id:
                raise KeyError(f"Artifact with id {artifact.id} not found.")

            old_artifact = self._by_id[artifact.id]

            if old_artifact.stable_key != artifact.stable_key:
                del self._by_stable_key[old_artifact.stable_key]
                self._by_stable_key[artifact.stable_key] = artifact

            if old_artifact.file != artifact.file:
                self._by_file[old_artifact.file].discard(artifact.id)
                self._by_file.setdefault(artifact.file, set()).add(artifact.id)

            if old_artifact.kind != artifact.kind:
                self._by_kind[old_artifact.kind].discard(artifact.id)
                self._by_kind.setdefault(artifact.kind, set()).add(artifact.id)

            self._by_id[artifact.id] = artifact

    def remove(self, artifact_id: str) -> None:
        """Remove an artifact by ID."""
        with self._lock:
            if artifact_id not in self._by_id:
                raise KeyError(f"Artifact with id {artifact_id} not found.")

            self.graph.remove_node(artifact_id)
            artifact = self._by_id.pop(artifact_id)
            del self._by_stable_key[artifact.stable_key]
            self._by_file[artifact.file].discard(artifact.id)
            self._by_kind[artifact.kind].discard(artifact.id)

    def get_by_id(self, artifact_id: str) -> Optional[Artifact]:
        """Lookup an artifact by ID."""
        with self._lock:
            return self._by_id.get(artifact_id)

    def get_by_stable_key(self, stable_key: str) -> Optional[Artifact]:
        """Lookup an artifact by stable key."""
        with self._lock:
            return self._by_stable_key.get(stable_key)

    def get_by_file(self, file_path: str) -> List[Artifact]:
        """Lookup artifacts by file."""
        with self._lock:
            ids = self._by_file.get(file_path, set())
            return [self._by_id[aid] for aid in ids]

    def get_by_kind(self, kind: str) -> List[Artifact]:
        """Lookup artifacts by kind."""
        with self._lock:
            ids = self._by_kind.get(kind, set())
            return [self._by_id[aid] for aid in ids]

    def clear(self) -> None:
        """Clear the registry."""
        with self._lock:
            self.graph.clear()
            self._by_id.clear()
            self._by_stable_key.clear()
            self._by_file.clear()
            self._by_kind.clear()
