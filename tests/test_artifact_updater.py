from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import pytest

from engine.domain.artifacts.changes import ChangeSet
from engine.domain.artifacts.update_result import UpdateResult
from engine.domain.artifacts.updater import ArtifactUpdater


@dataclass(frozen=True)
class DictionaryArtifact:
    entities: Mapping[str, str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "entities", MappingProxyType(dict(self.entities)))


class DictionaryArtifactUpdater(ArtifactUpdater[DictionaryArtifact, ChangeSet[str]]):
    """Reference updater used only to verify the abstract contract."""

    def __init__(self, replacements: Mapping[str, str] | None = None) -> None:
        self._replacements = dict(replacements or {})

    def update(self, previous: DictionaryArtifact, changes: ChangeSet[str]) -> UpdateResult[DictionaryArtifact]:
        next_entities = dict(previous.entities)
        for entity_id in changes.deleted:
            next_entities.pop(entity_id, None)
        for entity_id in changes.added | changes.updated:
            next_entities[entity_id] = self._replacements[entity_id]
        return UpdateResult(artifact=DictionaryArtifact(next_entities), changes=changes)


def test_no_op_update_returns_a_new_artifact_snapshot_and_empty_change_set():
    previous = DictionaryArtifact({"A": "old"})
    changes = ChangeSet(layer="semantic")

    result = DictionaryArtifactUpdater().update(previous, changes)

    assert result.artifact is not previous
    assert result.artifact.entities == {"A": "old"}
    assert result.changes.is_empty()


def test_add_update_and_delete_return_new_state_and_the_output_change_set():
    previous = DictionaryArtifact({"A": "old", "B": "remove"})
    changes = ChangeSet(
        layer="semantic",
        added={"C"},
        updated={"A"},
        deleted={"B"},
    )

    result = DictionaryArtifactUpdater({"A": "new", "C": "created"}).update(previous, changes)

    assert result.artifact.entities == {"A": "new", "C": "created"}
    assert previous.entities == {"A": "old", "B": "remove"}
    assert result.changes is changes


def test_affected_entities_remain_distinct_from_direct_changes():
    previous = DictionaryArtifact({"C1": "left", "C2": "removed", "C3": "right"})
    changes = ChangeSet(layer="cfg", deleted={"C2"}, affected={"C1", "C3"})

    result = DictionaryArtifactUpdater().update(previous, changes)

    assert result.artifact.entities == {"C1": "left", "C3": "right"}
    assert result.changes.deleted == frozenset({"C2"})
    assert result.changes.affected == frozenset({"C1", "C3"})


def test_previous_artifact_is_immutable_and_not_modified_in_place():
    previous = DictionaryArtifact({"A": "old"})
    changes = ChangeSet(layer="semantic", updated={"A"})

    with pytest.raises(TypeError):
        previous.entities["A"] = "mutated"

    result = DictionaryArtifactUpdater({"A": "new"}).update(previous, changes)
    assert previous.entities["A"] == "old"
    assert result.artifact.entities["A"] == "new"


def test_reference_implementation_returns_update_result_contract():
    result = DictionaryArtifactUpdater({"A": "created"}).update(
        DictionaryArtifact({}),
        ChangeSet(layer="semantic", added={"A"}),
    )

    assert isinstance(result, UpdateResult)
    assert isinstance(result.changes, ChangeSet)
