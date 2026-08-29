"""Reverse provenance index for incremental source-to-artifact invalidation."""

from __future__ import annotations

import threading
from collections.abc import Iterable, Mapping
from typing import TypeAlias
from uuid import UUID


ASTOriginId: TypeAlias = str | UUID
DerivedEntityId: TypeAlias = str


class ProvenanceIndex:
    """Maintain direct source-AST to derived-entity provenance relationships.

    This is intentionally an index, not a dependency graph: it records only
    direct origins and provides O(1)-indexed reverse lookup for a changed AST
    node.  Returned sets are immutable snapshots.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._derived_by_origin: dict[ASTOriginId, set[DerivedEntityId]] = {}
        self._origins_by_derived: dict[DerivedEntityId, set[ASTOriginId]] = {}

    def register(self, derived_entity_id: DerivedEntityId, ast_origin_ids: Iterable[ASTOriginId]) -> None:
        """Add direct provenance from one or more AST origins to an entity.

        Registration is additive and idempotent, so a duplicate registration
        does not create duplicate relationships.  Replacing provenance is an
        explicit remove followed by registration.
        """

        self._validate_derived_id(derived_entity_id)
        origins = self._validated_origins(ast_origin_ids)
        with self._lock:
            derived_origins = self._origins_by_derived.setdefault(derived_entity_id, set())
            for origin_id in origins:
                derived_origins.add(origin_id)
                self._derived_by_origin.setdefault(origin_id, set()).add(derived_entity_id)

    def register_batch(self, registrations: Mapping[DerivedEntityId, Iterable[ASTOriginId]]) -> None:
        """Atomically register a mapping of derived entities to their origins."""

        if not isinstance(registrations, Mapping):
            raise TypeError("registrations must be a mapping")
        normalized = [
            (derived_entity_id, self._validated_origins(origin_ids))
            for derived_entity_id, origin_ids in registrations.items()
        ]
        for derived_entity_id, _ in normalized:
            self._validate_derived_id(derived_entity_id)

        with self._lock:
            for derived_entity_id, origins in normalized:
                derived_origins = self._origins_by_derived.setdefault(derived_entity_id, set())
                for origin_id in origins:
                    derived_origins.add(origin_id)
                    self._derived_by_origin.setdefault(origin_id, set()).add(derived_entity_id)

    def remove(self, derived_entity_id: DerivedEntityId, ast_origin_ids: Iterable[ASTOriginId] | None = None) -> None:
        """Remove all, or selected, direct provenance for a derived entity."""

        self._validate_derived_id(derived_entity_id)
        origins_to_remove = None if ast_origin_ids is None else self._validated_origins(ast_origin_ids)
        with self._lock:
            registered_origins = self._origins_by_derived.get(derived_entity_id)
            if registered_origins is None:
                return

            selected_origins = set(registered_origins) if origins_to_remove is None else registered_origins & origins_to_remove
            for origin_id in selected_origins:
                registered_origins.discard(origin_id)
                derived_entities = self._derived_by_origin[origin_id]
                derived_entities.discard(derived_entity_id)
                if not derived_entities:
                    del self._derived_by_origin[origin_id]
            if not registered_origins:
                del self._origins_by_derived[derived_entity_id]

    def remove_batch(self, derived_entity_ids: Iterable[DerivedEntityId]) -> None:
        """Remove all provenance for each supplied derived entity."""

        entity_ids = tuple(derived_entity_ids)
        for derived_entity_id in entity_ids:
            self._validate_derived_id(derived_entity_id)
        with self._lock:
            for derived_entity_id in entity_ids:
                registered_origins = self._origins_by_derived.pop(derived_entity_id, set())
                for origin_id in registered_origins:
                    derived_entities = self._derived_by_origin[origin_id]
                    derived_entities.discard(derived_entity_id)
                    if not derived_entities:
                        del self._derived_by_origin[origin_id]

    def lookup_derived(self, ast_origin_id: ASTOriginId) -> frozenset[DerivedEntityId]:
        """Return entities directly derived from one AST origin."""

        self._validate_origin_id(ast_origin_id)
        with self._lock:
            return frozenset(self._derived_by_origin.get(ast_origin_id, ()))

    def lookup_origins(self, derived_entity_id: DerivedEntityId) -> frozenset[ASTOriginId]:
        """Return direct AST origins recorded for one derived entity."""

        self._validate_derived_id(derived_entity_id)
        with self._lock:
            return frozenset(self._origins_by_derived.get(derived_entity_id, ()))

    register_provenance = register
    remove_provenance = remove
    get_derived_entities = lookup_derived
    get_origins = lookup_origins

    @staticmethod
    def _validated_origins(ast_origin_ids: Iterable[ASTOriginId]) -> frozenset[ASTOriginId]:
        if isinstance(ast_origin_ids, (str, UUID)):
            raise TypeError("ast_origin_ids must be an iterable of origin IDs")
        origins = frozenset(ast_origin_ids)
        if not origins:
            raise ValueError("at least one AST origin ID is required")
        for origin_id in origins:
            ProvenanceIndex._validate_origin_id(origin_id)
        return origins

    @staticmethod
    def _validate_derived_id(derived_entity_id: DerivedEntityId) -> None:
        if not isinstance(derived_entity_id, str) or not derived_entity_id.strip():
            raise ValueError("derived_entity_id is required")

    @staticmethod
    def _validate_origin_id(ast_origin_id: ASTOriginId) -> None:
        if isinstance(ast_origin_id, UUID):
            return
        if not isinstance(ast_origin_id, str) or not ast_origin_id.strip():
            raise ValueError("ast_origin_id must be a non-empty string or UUID")
