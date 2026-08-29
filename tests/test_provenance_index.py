from uuid import uuid4

from engine.incremental.provenance import ProvenanceIndex


def test_one_ast_origin_maps_to_one_derived_entity():
    index = ProvenanceIndex()
    index.register("semantic-1", ["ast-1"])

    assert index.lookup_derived("ast-1") == frozenset({"semantic-1"})
    assert index.lookup_origins("semantic-1") == frozenset({"ast-1"})


def test_many_ast_origins_map_to_one_derived_entity():
    index = ProvenanceIndex()
    index.register("cfg-1", ["ast-1", "ast-2", "ast-3"])

    assert index.lookup_derived("ast-1") == frozenset({"cfg-1"})
    assert index.lookup_derived("ast-2") == frozenset({"cfg-1"})
    assert index.lookup_origins("cfg-1") == frozenset({"ast-1", "ast-2", "ast-3"})


def test_one_ast_origin_maps_to_many_derived_entities():
    index = ProvenanceIndex()
    index.register("semantic-1", ["ast-1"])
    index.register("cfg-1", ["ast-1"])
    index.register("finding-1", ["ast-1"])

    assert index.lookup_derived("ast-1") == frozenset({"semantic-1", "cfg-1", "finding-1"})


def test_remove_provenance_updates_both_lookup_directions():
    index = ProvenanceIndex()
    index.register("cfg-1", ["ast-1", "ast-2"])

    index.remove("cfg-1", ["ast-1"])

    assert index.lookup_derived("ast-1") == frozenset()
    assert index.lookup_derived("ast-2") == frozenset({"cfg-1"})
    assert index.lookup_origins("cfg-1") == frozenset({"ast-2"})


def test_lookup_after_derived_entity_deletion_is_empty():
    index = ProvenanceIndex()
    index.register("finding-1", ["ast-1"])

    index.remove("finding-1")

    assert index.lookup_derived("ast-1") == frozenset()
    assert index.lookup_origins("finding-1") == frozenset()


def test_batch_registration_and_removal():
    index = ProvenanceIndex()
    origin_uuid = uuid4()
    index.register_batch({
        "semantic-1": ["ast-1", origin_uuid],
        "cfg-1": ["ast-1"],
    })

    assert index.lookup_derived("ast-1") == frozenset({"semantic-1", "cfg-1"})
    assert index.lookup_derived(origin_uuid) == frozenset({"semantic-1"})

    index.remove_batch(["semantic-1", "cfg-1"])
    assert index.lookup_derived("ast-1") == frozenset()


def test_unknown_ast_origin_returns_an_empty_snapshot():
    assert ProvenanceIndex().lookup_derived("missing-ast") == frozenset()


def test_duplicate_registration_is_idempotent():
    index = ProvenanceIndex()
    index.register("semantic-1", ["ast-1"])
    index.register("semantic-1", ["ast-1"])

    assert index.lookup_derived("ast-1") == frozenset({"semantic-1"})
    assert index.lookup_origins("semantic-1") == frozenset({"ast-1"})
