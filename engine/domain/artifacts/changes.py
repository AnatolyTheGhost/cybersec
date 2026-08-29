"""Immutable change contracts exchanged between incremental artifact layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, Hashable, TypeVar


EntityIdT = TypeVar("EntityIdT", bound=Hashable)
EdgeIdT = TypeVar("EdgeIdT", bound=Hashable)


def _validate_disjoint(*groups: frozenset[Hashable]) -> None:
    for index, group in enumerate(groups):
        for other in groups[index + 1 :]:
            if overlap := group & other:
                raise ValueError(f"ChangeSet categories must be disjoint; overlap: {overlap!r}")


@dataclass(frozen=True, slots=True)
class ChangeSet(Generic[EntityIdT]):
    """Net entity changes emitted by one named artifact layer.

    ``affected`` identifies existing entities whose relationships or state
    need rebuilding even though they are not themselves added, updated, or
    deleted.  It is deliberately distinct from direct changes.
    """

    layer: str
    added: frozenset[EntityIdT] = field(default_factory=frozenset)
    updated: frozenset[EntityIdT] = field(default_factory=frozenset)
    deleted: frozenset[EntityIdT] = field(default_factory=frozenset)
    affected: frozenset[EntityIdT] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not isinstance(self.layer, str) or not self.layer.strip():
            raise ValueError("layer is required")

        for field_name in ("added", "updated", "deleted", "affected"):
            object.__setattr__(self, field_name, frozenset(getattr(self, field_name)))

        _validate_disjoint(self.added, self.updated, self.deleted, self.affected)

    def is_empty(self) -> bool:
        """Return whether this layer has neither direct nor affected changes."""

        return not (self.added or self.updated or self.deleted or self.affected)

    def merge(self, other: "ChangeSet[EntityIdT]") -> "ChangeSet[EntityIdT]":
        """Combine independent changes from the same artifact layer.

        Direct-change categories are intentionally not reinterpreted here: an
        entity classified differently by both inputs needs layer-specific
        context and is rejected.  A direct change supersedes an ``affected``
        marker for the same entity in the merged result.
        """

        if not isinstance(other, ChangeSet):
            raise TypeError("other must be a ChangeSet")
        if self.layer != other.layer:
            raise ValueError("only ChangeSets for the same layer can be merged")

        added = self.added | other.added
        updated = self.updated | other.updated
        deleted = self.deleted | other.deleted
        _validate_disjoint(added, updated, deleted)

        changed = added | updated | deleted
        affected = (self.affected | other.affected) - changed
        return ChangeSet(
            layer=self.layer,
            added=added,
            updated=updated,
            deleted=deleted,
            affected=affected,
        )


@dataclass(frozen=True, slots=True)
class GraphChangeSet(ChangeSet[EntityIdT], Generic[EntityIdT, EdgeIdT]):
    """Optional extension for layers that model addressable graph edges."""

    added_edges: frozenset[EdgeIdT] = field(default_factory=frozenset)
    updated_edges: frozenset[EdgeIdT] = field(default_factory=frozenset)
    deleted_edges: frozenset[EdgeIdT] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("added_edges", "updated_edges", "deleted_edges"):
            object.__setattr__(self, field_name, frozenset(getattr(self, field_name)))
        _validate_disjoint(self.added_edges, self.updated_edges, self.deleted_edges)

    def is_empty(self) -> bool:
        return super().is_empty() and not (self.added_edges or self.updated_edges or self.deleted_edges)


@dataclass(frozen=True, slots=True)
class SourceChangeSet(ChangeSet[str]):
    layer: str = field(default="source", init=False)


@dataclass(frozen=True, slots=True)
class SemanticChangeSet(ChangeSet[str]):
    layer: str = field(default="semantic", init=False)


@dataclass(frozen=True, slots=True)
class CFGChangeSet(ChangeSet[str]):
    layer: str = field(default="cfg", init=False)


@dataclass(frozen=True, slots=True)
class DataFlowChangeSet(ChangeSet[str]):
    layer: str = field(default="data_flow", init=False)


@dataclass(frozen=True, slots=True)
class FindingChangeSet(ChangeSet[str]):
    layer: str = field(default="finding", init=False)
