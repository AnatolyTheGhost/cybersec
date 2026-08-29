"""Immutable source/AST mutation contracts for incremental analysis.

These contracts describe a change to source state only.  Consumers are
responsible for applying a mutation and updating any derived artifacts.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, TypeAlias
from uuid import UUID, uuid4


EntityId: TypeAlias = str
VersionId: TypeAlias = str
MutationId: TypeAlias = UUID
BatchId: TypeAlias = UUID


class MutationKind(str, Enum):
    """The operation applied to one source/AST entity."""

    ADD = "ADD"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


def _freeze_payload(value: Any) -> Any:
    """Recursively freeze payload values so a Mutation is truly immutable."""

    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_payload(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_payload(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze_payload(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class Mutation:
    """One source/AST change made against a specific source-state version.

    ``payload`` is the new node/source representation for ``ADD`` and
    ``UPDATE``.  It is intentionally absent for ``DELETE``; metadata that is
    unrelated to a replacement node belongs to the event that creates this
    contract, not to analysis artifacts.
    """

    kind: MutationKind
    entity_id: EntityId
    base_version_id: VersionId
    payload: Mapping[str, Any] | None = None
    mutation_id: MutationId = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not isinstance(self.kind, MutationKind):
            raise TypeError("kind must be a MutationKind")
        if not isinstance(self.mutation_id, UUID):
            raise TypeError("mutation_id must be a UUID")
        if not isinstance(self.base_version_id, str) or not self.base_version_id.strip():
            raise ValueError("base_version_id is required")
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("entity_id is required")

        if self.kind is MutationKind.DELETE:
            if self.payload is not None:
                raise ValueError("DELETE mutations must not include a new node payload")
            return

        if self.payload is None:
            raise ValueError(f"{self.kind.value} mutations require a new node payload")
        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")
        if not self.payload:
            raise ValueError(f"{self.kind.value} mutations require a non-empty node payload")

        object.__setattr__(self, "payload", _freeze_payload(self.payload))


@dataclass(frozen=True, slots=True)
class MutationBatch:
    """An ordered, atomic group of source/AST mutations for one base version.

    A batch is an input to incremental processing, not an analysis run.  It
    preserves every operation, including multiple or conflicting operations on
    one entity, so a separate MutationNormalizer can resolve them later.
    """

    base_version_id: VersionId
    mutations: tuple[Mutation, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)
    batch_id: BatchId = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if not isinstance(self.batch_id, UUID):
            raise TypeError("batch_id must be a UUID")
        if not isinstance(self.base_version_id, str) or not self.base_version_id.strip():
            raise ValueError("base_version_id is required")

        mutations = tuple(self.mutations)
        if not mutations:
            raise ValueError("mutations must not be empty")
        if not all(isinstance(mutation, Mutation) for mutation in mutations):
            raise TypeError("mutations must contain only Mutation instances")
        if any(mutation.base_version_id != self.base_version_id for mutation in mutations):
            raise ValueError("all mutations must use the batch base_version_id")

        mutation_ids = [mutation.mutation_id for mutation in mutations]
        if len(set(mutation_ids)) != len(mutation_ids):
            raise ValueError("mutation IDs must be unique within a batch")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        object.__setattr__(self, "mutations", mutations)
        object.__setattr__(self, "metadata", _freeze_payload(self.metadata))
