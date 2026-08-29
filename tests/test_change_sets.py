from dataclasses import FrozenInstanceError

import pytest

from engine.domain.artifacts.changes import (
    CFGChangeSet,
    ChangeSet,
    DataFlowChangeSet,
    FindingChangeSet,
    GraphChangeSet,
    SemanticChangeSet,
    SourceChangeSet,
)


def test_change_set_keeps_changed_and_affected_entities_distinct():
    changes = ChangeSet(
        layer="cfg",
        deleted={"C2"},
        affected={"C1", "C3"},
    )

    assert changes.deleted == frozenset({"C2"})
    assert changes.affected == frozenset({"C1", "C3"})
    assert not changes.is_empty()


def test_change_set_is_empty_when_all_categories_are_empty():
    assert ChangeSet(layer="semantic").is_empty()


@pytest.mark.parametrize(
    ("kwargs",),
    [
        ({"added": {"A"}, "updated": {"A"}},),
        ({"updated": {"A"}, "deleted": {"A"}},),
        ({"deleted": {"A"}, "affected": {"A"}},),
    ],
)
def test_change_set_rejects_overlapping_categories(kwargs):
    with pytest.raises(ValueError, match="categories must be disjoint"):
        ChangeSet(layer="semantic", **kwargs)


def test_change_set_is_immutable():
    changes = ChangeSet(layer="source", added={"A"})

    with pytest.raises(FrozenInstanceError):
        changes.layer = "semantic"
    with pytest.raises(AttributeError):
        changes.added.add("B")


def test_merge_combines_independent_changes_and_removes_stale_affected_marker():
    left = ChangeSet(layer="semantic", added={"A"}, affected={"B"})
    right = ChangeSet(layer="semantic", updated={"B"}, deleted={"C"})

    merged = left.merge(right)

    assert merged.added == frozenset({"A"})
    assert merged.updated == frozenset({"B"})
    assert merged.deleted == frozenset({"C"})
    assert merged.affected == frozenset()


def test_merge_rejects_different_layers_and_conflicting_classifications():
    with pytest.raises(ValueError, match="same layer"):
        ChangeSet(layer="source", added={"A"}).merge(ChangeSet(layer="semantic", added={"B"}))
    with pytest.raises(ValueError, match="categories must be disjoint"):
        ChangeSet(layer="source", added={"A"}).merge(ChangeSet(layer="source", deleted={"A"}))


def test_layer_specific_change_sets_fix_their_layer_name():
    assert SourceChangeSet(added={"source-1"}).layer == "source"
    assert SemanticChangeSet(updated={"semantic-1"}).layer == "semantic"
    assert CFGChangeSet(deleted={"cfg-1"}).layer == "cfg"
    assert DataFlowChangeSet(affected={"flow-1"}).layer == "data_flow"
    assert FindingChangeSet(added={"finding-1"}).layer == "finding"


def test_graph_change_set_can_track_edges_without_knowing_edge_structure():
    changes = GraphChangeSet(
        layer="cfg",
        deleted={"C2"},
        affected={"C1", "C3"},
        deleted_edges={("C1", "C2"), ("C2", "C3")},
    )

    assert changes.deleted_edges == frozenset({("C1", "C2"), ("C2", "C3")})
    with pytest.raises(ValueError, match="categories must be disjoint"):
        GraphChangeSet(layer="cfg", added_edges={("A", "B")}, deleted_edges={("A", "B")})
