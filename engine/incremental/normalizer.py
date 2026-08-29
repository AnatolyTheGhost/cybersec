"""Normalization of source/AST mutation batches before incremental analysis."""

from __future__ import annotations

from dataclasses import dataclass

from .mutations import Mutation, MutationBatch, MutationKind, VersionId


class MutationNormalizationError(ValueError):
    """Raised when a mutation sequence cannot be reduced without AST context."""


@dataclass(frozen=True, slots=True)
class NormalizedMutationSet:
    """The deterministic net source/AST effect of one MutationBatch.

    An empty ``mutations`` tuple is valid: for example, ``ADD`` followed by
    ``DELETE`` has no effect relative to the batch's base version.
    """

    base_version_id: VersionId
    mutations: tuple[Mutation, ...]


class MutationNormalizer:
    """Reduce per-entity source/AST operations without performing analysis."""

    def normalize(self, batch: MutationBatch) -> NormalizedMutationSet:
        if not isinstance(batch, MutationBatch):
            raise TypeError("batch must be a MutationBatch")

        net_mutations: dict[str, Mutation | None] = {}
        for mutation in batch.mutations:
            current = net_mutations.get(mutation.entity_id)
            if mutation.entity_id not in net_mutations:
                net_mutations[mutation.entity_id] = mutation
                continue

            net_mutations[mutation.entity_id] = self._reduce(current, mutation)

        return NormalizedMutationSet(
            base_version_id=batch.base_version_id,
            mutations=tuple(mutation for mutation in net_mutations.values() if mutation is not None),
        )

    @staticmethod
    def _reduce(current: Mutation | None, next_mutation: Mutation) -> Mutation | None:
        """Reduce one entity's next operation, preserving first-seen order.

        The retained mutation ID is the first operation's ID.  This makes the
        normalized form deterministic without inventing a new source mutation.
        """

        if current is None:
            if next_mutation.kind is MutationKind.ADD:
                return next_mutation
            raise MutationNormalizationError(
                f"{next_mutation.kind.value} after ADD then DELETE for {next_mutation.entity_id!r} "
                "cannot be normalized without entity context"
            )

        if current.kind is MutationKind.ADD:
            if next_mutation.kind is MutationKind.UPDATE:
                return Mutation(
                    kind=MutationKind.ADD,
                    entity_id=current.entity_id,
                    base_version_id=current.base_version_id,
                    payload=next_mutation.payload,
                    mutation_id=current.mutation_id,
                )
            if next_mutation.kind is MutationKind.DELETE:
                return None
            raise MutationNormalizationError(
                f"ADD after ADD for {current.entity_id!r} cannot be normalized without entity context"
            )

        if current.kind is MutationKind.UPDATE:
            if next_mutation.kind is MutationKind.UPDATE:
                return Mutation(
                    kind=MutationKind.UPDATE,
                    entity_id=current.entity_id,
                    base_version_id=current.base_version_id,
                    payload=next_mutation.payload,
                    mutation_id=current.mutation_id,
                )
            if next_mutation.kind is MutationKind.DELETE:
                return Mutation(
                    kind=MutationKind.DELETE,
                    entity_id=current.entity_id,
                    base_version_id=current.base_version_id,
                    mutation_id=current.mutation_id,
                )
            raise MutationNormalizationError(
                f"ADD after UPDATE for {current.entity_id!r} cannot be normalized without entity context"
            )

        raise MutationNormalizationError(
            f"{next_mutation.kind.value} after DELETE for {current.entity_id!r} "
            "cannot be normalized without entity context"
        )
