"""Generic result contract for an incremental artifact-layer update."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

from .changes import ChangeSet


TArtifact = TypeVar("TArtifact")


@dataclass(frozen=True, slots=True)
class UpdateResult(Generic[TArtifact]):
    """The rebuilt artifact and its net layer-local changes.

    The contract deliberately holds no execution, session, or provenance
    state.  It can therefore be used by source, semantic, and future artifact
    updaters alike.
    """

    artifact: TArtifact
    changes: ChangeSet

    def __post_init__(self) -> None:
        if not isinstance(self.changes, ChangeSet):
            raise TypeError("changes must be a ChangeSet")
