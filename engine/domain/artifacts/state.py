import threading
from typing import Dict, Iterable


class ArtifactStateManager:
    """
    Tracks the state and version of addressable artifacts.
    Keeps state independent of the frozen artifact representations.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._dirty_set: set[str] = set()
        self._versions: Dict[str, int] = {}

    def is_dirty(self, artifact_id: str) -> bool:
        """Check if an artifact is currently dirty."""
        with self._lock:
            return artifact_id in self._dirty_set

    def get_version(self, artifact_id: str) -> int:
        """Get the current version of an artifact (defaults to 1)."""
        with self._lock:
            return self._versions.get(artifact_id, 1)

    def mark_dirty(self, artifact_ids: Iterable[str]) -> None:
        """Mark one or multiple artifacts as dirty."""
        with self._lock:
            self._dirty_set.update(artifact_ids)

    def mark_clean(self, artifact_ids: Iterable[str]) -> None:
        """Mark one or multiple artifacts as clean."""
        with self._lock:
            self._dirty_set.difference_update(artifact_ids)

    def bump_version(self, artifact_id: str) -> int:
        """
        Increment the version of an artifact, typically called
        after successfully rebuilding it.
        Returns the new version.
        """
        with self._lock:
            new_version = self.get_version(artifact_id) + 1
            self._versions[artifact_id] = new_version
            return new_version

    def remove(self, artifact_id: str) -> None:
        """Remove state for an artifact."""
        with self._lock:
            self._dirty_set.discard(artifact_id)
            self._versions.pop(artifact_id, None)

    def clear(self) -> None:
        """Clear all state."""
        with self._lock:
            self._dirty_set.clear()
            self._versions.clear()
