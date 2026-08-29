"""Generic contract for incremental derived-artifact updates."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .changes import ChangeSet
from .update_result import UpdateResult


TArtifact = TypeVar("TArtifact")
TInputChangeSet = TypeVar("TInputChangeSet", bound=ChangeSet)


class ArtifactUpdater(ABC, Generic[TArtifact, TInputChangeSet]):
    """Transform an artifact snapshot and layer-local changes into a new snapshot.

    Implementations own their artifact-specific relationship handling.  This
    base contract deliberately knows nothing about mutations, provenance,
    global orchestration, dependency graphs, or downstream updaters.
    """

    @abstractmethod
    def update(self, previous: TArtifact, changes: TInputChangeSet) -> UpdateResult[TArtifact]:
        """Return a new artifact snapshot and changes for the next layer."""

        ...
