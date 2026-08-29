import pytest

from engine.incremental.mutations import Mutation, MutationBatch, MutationKind
from engine.incremental.normalizer import (
    MutationNormalizer,
    MutationNormalizationError,
)


def _mutation(kind: MutationKind, entity_id: str, payload: dict | None = None) -> Mutation:
    return Mutation(
        kind=kind,
        entity_id=entity_id,
        base_version_id="source-v1",
        payload=payload,
    )


def _normalize(*mutations: Mutation):
    batch = MutationBatch(base_version_id="source-v1", mutations=mutations)
    return MutationNormalizer().normalize(batch)


def test_repeated_updates_reduce_to_final_update_without_mutating_batch():
    first = _mutation(MutationKind.UPDATE, "A", {"value": "first"})
    second = _mutation(MutationKind.UPDATE, "A", {"value": "final"})
    batch = MutationBatch(base_version_id="source-v1", mutations=(first, second))

    normalized = MutationNormalizer().normalize(batch)

    assert normalized.mutations[0].kind is MutationKind.UPDATE
    assert normalized.mutations[0].payload == {"value": "final"}
    assert normalized.mutations[0].mutation_id == first.mutation_id
    assert batch.mutations == (first, second)


def test_add_then_update_reduces_to_add_with_final_payload():
    normalized = _normalize(
        _mutation(MutationKind.ADD, "A", {"value": "first"}),
        _mutation(MutationKind.UPDATE, "A", {"value": "final"}),
    )

    assert len(normalized.mutations) == 1
    assert normalized.mutations[0].kind is MutationKind.ADD
    assert normalized.mutations[0].payload == {"value": "final"}


def test_add_then_delete_reduces_to_no_op():
    normalized = _normalize(
        _mutation(MutationKind.ADD, "A", {"value": "created"}),
        _mutation(MutationKind.DELETE, "A"),
    )

    assert normalized.mutations == ()


def test_update_then_delete_reduces_to_delete():
    normalized = _normalize(
        _mutation(MutationKind.UPDATE, "A", {"value": "changed"}),
        _mutation(MutationKind.DELETE, "A"),
    )

    assert len(normalized.mutations) == 1
    assert normalized.mutations[0].kind is MutationKind.DELETE
    assert normalized.mutations[0].payload is None


def test_delete_then_update_requires_entity_context():
    with pytest.raises(MutationNormalizationError, match="UPDATE after DELETE"):
        _normalize(
            _mutation(MutationKind.DELETE, "A"),
            _mutation(MutationKind.UPDATE, "A", {"value": "restored"}),
        )


def test_independent_nodes_are_normalized_in_first_seen_order():
    normalized = _normalize(
        _mutation(MutationKind.UPDATE, "B", {"value": "old"}),
        _mutation(MutationKind.ADD, "A", {"value": "created"}),
        _mutation(MutationKind.UPDATE, "B", {"value": "new"}),
    )

    assert [mutation.entity_id for mutation in normalized.mutations] == ["B", "A"]
    assert normalized.mutations[0].payload == {"value": "new"}


@pytest.mark.parametrize(
    ("first", "second", "message"),
    [
        (MutationKind.ADD, MutationKind.ADD, "ADD after ADD"),
        (MutationKind.UPDATE, MutationKind.ADD, "ADD after UPDATE"),
        (MutationKind.DELETE, MutationKind.ADD, "ADD after DELETE"),
    ],
)
def test_ambiguous_sequences_are_rejected(first, second, message):
    first_payload = {"value": "first"} if first is not MutationKind.DELETE else None
    second_payload = {"value": "second"} if second is not MutationKind.DELETE else None

    with pytest.raises(MutationNormalizationError, match=message):
        _normalize(
            _mutation(first, "A", first_payload),
            _mutation(second, "A", second_payload),
        )
