from dataclasses import FrozenInstanceError

import pytest

from engine.domain.artifacts.changes import ChangeSet, SourceChangeSet
from engine.domain.artifacts.models import Artifact
from engine.domain.artifacts.update_result import UpdateResult


def test_update_result_contains_an_artifact_and_its_changes():
    artifact = Artifact(id="artifact-1", stable_key="file:main.py", kind="source", file="main.py")
    changes = SourceChangeSet(updated={"node-1"})

    result: UpdateResult[Artifact] = UpdateResult(artifact=artifact, changes=changes)

    assert result.artifact is artifact
    assert result.changes is changes


def test_update_result_accepts_an_empty_change_set_for_any_artifact_type():
    ast_artifact = {"kind": "Module", "id": "ast-1"}

    result: UpdateResult[dict[str, str]] = UpdateResult(
        artifact=ast_artifact,
        changes=ChangeSet(layer="source"),
    )

    assert result.changes.is_empty()
    assert result.artifact == ast_artifact


def test_update_result_is_immutable_and_validates_changes_contract():
    result = UpdateResult(artifact="semantic-ast", changes=ChangeSet(layer="semantic"))

    with pytest.raises(FrozenInstanceError):
        result.artifact = "different-ast"
    with pytest.raises(TypeError, match="changes must be a ChangeSet"):
        UpdateResult(artifact="semantic-ast", changes={"updated": {"node-1"}})
