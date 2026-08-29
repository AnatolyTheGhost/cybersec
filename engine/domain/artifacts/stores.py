from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from .models import Artifact
from .registry import ArtifactRegistry

T = TypeVar("T", bound=Artifact)

class BaseArtifactStore(ABC, Generic[T]):
    """
    Abstract base class for dedicated artifact stores.
    Internally synchronizes with the ArtifactRegistry.
    """
    def __init__(self, registry: ArtifactRegistry):
        self._registry = registry

    @abstractmethod
    def insert(self, artifact: T) -> None:
        """Insert a new artifact into the store and registry."""
        self._registry.register(artifact)

    @abstractmethod
    def update(self, artifact: T) -> None:
        """Update an existing artifact in the store and registry."""
        self._registry.update(artifact)

    @abstractmethod
    def remove(self, artifact_id: str) -> None:
        """Remove an artifact from the store and registry."""
        self._registry.remove(artifact_id)

    @abstractmethod
    def get(self, artifact_id: str) -> Optional[T]:
        """Get an artifact by ID."""
        artifact = self._registry.get_by_id(artifact_id)
        return artifact if artifact is not None else None

    @abstractmethod
    def find_by_file(self, file_path: str) -> List[T]:
        """Find artifacts associated with a specific file."""
        return self._registry.get_by_file(file_path)

    @abstractmethod
    def find_by_stable_key(self, stable_key: str) -> Optional[T]:
        """Find an artifact by its stable key."""
        artifact = self._registry.get_by_stable_key(stable_key)
        return artifact if artifact is not None else None


class InMemoryArtifactStore(BaseArtifactStore[T]):
    """
    In-memory implementation of the artifact store, proxying directly to the registry.
    """
    def insert(self, artifact: T) -> None:
        super().insert(artifact)

    def update(self, artifact: T) -> None:
        super().update(artifact)

    def remove(self, artifact_id: str) -> None:
        super().remove(artifact_id)

    def get(self, artifact_id: str) -> Optional[T]:
        return super().get(artifact_id)

    def find_by_file(self, file_path: str) -> List[T]:
        # Need to filter because registry returns all Artifacts, we want type T but Python's
        # generics aren't available at runtime. The registry itself doesn't guarantee type.
        # In a real implementation we might want store-specific filtering if multiple types
        # share the same store, but usually each store handles one kind.
        # We rely on the registry's storage.
        # A more robust check could be added if needed.
        return super().find_by_file(file_path)

    def find_by_stable_key(self, stable_key: str) -> Optional[T]:
        return super().find_by_stable_key(stable_key)
