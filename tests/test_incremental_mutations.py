from dataclasses import FrozenInstanceError
from uuid import UUID, uuid4

import pytest

from engine.incremental.mutations import Mutation, MutationBatch, MutationKind


def test_add_mutation_describes_a_new_source_entity():
    mutation = Mutation(
        kind=MutationKind.ADD,
        entity_id="node-new",
        base_version_id="source-v1",
        payload={"kind": "FunctionDef", "name": "authenticate"},
    )

    assert isinstance(mutation.mutation_id, UUID)
    assert mutation.payload == {"kind": "FunctionDef", "name": "authenticate"}


def test_update_mutation_identifies_existing_entity_and_replacement_payload():
    mutation = Mutation(
        kind=MutationKind.UPDATE,
        entity_id="node-existing",
        base_version_id="source-v4",
        payload={"kind": "Call", "callee": "sanitize"},
    )

    assert mutation.entity_id == "node-existing"
    assert mutation.payload["callee"] == "sanitize"


def test_delete_mutation_has_no_new_node_payload():
    mutation = Mutation(
        kind=MutationKind.DELETE,
        entity_id="node-removed",
        base_version_id="source-v4",
    )

    assert mutation.payload is None


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"kind": MutationKind.ADD, "payload": None}, "ADD mutations require"),
        ({"kind": MutationKind.UPDATE, "entity_id": "", "payload": {"kind": "Name"}}, "entity_id is required"),
        ({"kind": MutationKind.DELETE, "payload": {"kind": "Name"}}, "DELETE mutations must not"),
        ({"kind": MutationKind.ADD, "base_version_id": "", "payload": {"kind": "Name"}}, "base_version_id is required"),
        ({"kind": MutationKind.ADD, "mutation_id": "not-a-uuid", "payload": {"kind": "Name"}}, "mutation_id must be a UUID"),
    ],
)
def test_invalid_mutation_states_are_rejected(kwargs, message):
    defaults = {"entity_id": "node-1", "base_version_id": "source-v1"}

    with pytest.raises((TypeError, ValueError), match=message):
        Mutation(**(defaults | kwargs))


def test_mutation_is_immutable_and_has_value_equality():
    mutation_id = uuid4()
    first = Mutation(
        kind=MutationKind.ADD,
        entity_id="node-1",
        base_version_id="source-v1",
        payload={"children": [{"kind": "Name"}]},
        mutation_id=mutation_id,
    )
    second = Mutation(
        kind=MutationKind.ADD,
        entity_id="node-1",
        base_version_id="source-v1",
        payload={"children": [{"kind": "Name"}]},
        mutation_id=mutation_id,
    )

    assert first == second
    with pytest.raises(FrozenInstanceError):
        first.entity_id = "node-2"
    with pytest.raises(TypeError):
        first.payload["kind"] = "Call"
    assert first.payload["children"] == ({"kind": "Name"},)


def _add_mutation(entity_id: str, base_version_id: str = "source-v1") -> Mutation:
    return Mutation(
        kind=MutationKind.ADD,
        entity_id=entity_id,
        base_version_id=base_version_id,
        payload={"kind": "Name", "name": entity_id},
    )


def test_batch_accepts_one_mutation():
    mutation = _add_mutation("node-1")

    batch = MutationBatch(base_version_id="source-v1", mutations=(mutation,))

    assert isinstance(batch.batch_id, UUID)
    assert batch.mutations == (mutation,)


def test_batch_preserves_order_for_multiple_mutations():
    first = _add_mutation("node-1")
    second = _add_mutation("node-2")

    batch = MutationBatch(base_version_id="source-v1", mutations=[first, second])

    assert batch.mutations == (first, second)


def test_batch_allows_multiple_mutations_for_one_node():
    add = _add_mutation("node-1")
    update = Mutation(
        kind=MutationKind.UPDATE,
        entity_id="node-1",
        base_version_id="source-v1",
        payload={"kind": "Name", "name": "renamed"},
    )

    batch = MutationBatch(base_version_id="source-v1", mutations=(add, update))

    assert [mutation.kind for mutation in batch.mutations] == [MutationKind.ADD, MutationKind.UPDATE]


def test_batch_retains_conflicting_operations_for_a_normalizer():
    update = Mutation(
        kind=MutationKind.UPDATE,
        entity_id="node-1",
        base_version_id="source-v1",
        payload={"kind": "Name", "name": "renamed"},
    )
    delete = Mutation(
        kind=MutationKind.DELETE,
        entity_id="node-1",
        base_version_id="source-v1",
    )

    batch = MutationBatch(base_version_id="source-v1", mutations=(update, delete))

    assert batch.mutations == (update, delete)


def test_batch_rejects_mutations_from_different_base_versions():
    with pytest.raises(ValueError, match="all mutations must use"):
        MutationBatch(
            base_version_id="source-v1",
            mutations=(_add_mutation("node-1"), _add_mutation("node-2", "source-v2")),
        )


def test_batch_rejects_empty_and_duplicate_mutation_ids():
    with pytest.raises(ValueError, match="mutations must not be empty"):
        MutationBatch(base_version_id="source-v1", mutations=())

    mutation_id = uuid4()
    first = Mutation(MutationKind.ADD, "node-1", "source-v1", {"kind": "Name"}, mutation_id)
    second = Mutation(MutationKind.ADD, "node-2", "source-v1", {"kind": "Name"}, mutation_id)
    with pytest.raises(ValueError, match="mutation IDs must be unique"):
        MutationBatch(base_version_id="source-v1", mutations=(first, second))


def test_batch_is_immutable_including_its_metadata():
    batch = MutationBatch(
        base_version_id="source-v1",
        mutations=[_add_mutation("node-1")],
        metadata={"source": {"editor": "vscode"}},
    )

    with pytest.raises(FrozenInstanceError):
        batch.base_version_id = "source-v2"
    with pytest.raises(TypeError):
        batch.metadata["source"] = "cli"
    with pytest.raises(TypeError):
        batch.metadata["source"]["editor"] = "cli"
