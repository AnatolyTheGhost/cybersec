from dataclasses import FrozenInstanceError

import pytest

from engine.incremental.version_repository import InMemoryVersionRepository
from engine.incremental.versioning import (
    ArtifactRef,
    VersionConflictError,
    VersionManager,
    VersionNotFoundError,
)


def _manifest(suffix: str = "v1") -> dict[str, ArtifactRef]:
    return {
        "ast": ArtifactRef(f"ast-{suffix}", "ast"),
        "semantic": ArtifactRef(f"semantic-{suffix}", "semantic"),
        "cfg": ArtifactRef(f"cfg-{suffix}", "cfg"),
        "data_flow": ArtifactRef(f"data-flow-{suffix}", "data_flow"),
    }


def _manager() -> VersionManager:
    return VersionManager(InMemoryVersionRepository())


def test_create_initial_version_and_lookup():
    manager = _manager()

    initial = manager.create_initial("project-1", _manifest())

    assert initial.published
    assert initial.parent_version_id is None
    assert manager.get_version(initial.version_id) is initial


def test_latest_returns_current_published_version():
    manager = _manager()
    initial = manager.create_initial("project-1", _manifest())

    assert manager.get_latest("project-1") is initial


def test_candidate_and_published_version_preserve_parent_child_lineage():
    manager = _manager()
    initial = manager.create_initial("project-1", _manifest())
    candidate = manager.create_candidate("project-1", initial.version_id, _manifest("v2"))

    committed = manager.commit(candidate, expected_parent=initial.version_id)

    assert committed.published
    assert committed.parent_version_id == initial.version_id
    assert [version.version_id for version in manager.get_lineage(committed.version_id)] == [
        committed.version_id,
        initial.version_id,
    ]


def test_artifact_references_are_available_for_one_project_version():
    manager = _manager()
    initial = manager.create_initial("project-1", _manifest())

    references = manager.get_artifact_references(initial.version_id)

    assert references["semantic"] == ArtifactRef("semantic-v1", "semantic")
    with pytest.raises(TypeError):
        references["semantic"] = ArtifactRef("other", "semantic")


def test_published_version_is_immutable():
    manager = _manager()
    initial = manager.create_initial("project-1", _manifest(), metadata={"source": {"branch": "main"}})

    with pytest.raises(FrozenInstanceError):
        initial.project_id = "other-project"
    with pytest.raises(TypeError):
        initial.metadata["source"]["branch"] = "feature"


def test_successful_atomic_commit_publishes_full_candidate_as_latest():
    manager = _manager()
    initial = manager.create_initial("project-1", _manifest())
    candidate = manager.create_candidate("project-1", initial.version_id, _manifest("v2"))

    committed = manager.commit(candidate, expected_parent=initial.version_id)

    assert manager.get_latest("project-1") is committed
    assert committed.artifact_manifest["data_flow"].artifact_id == "data-flow-v2"


def test_failed_commit_leaves_previous_latest_version_untouched():
    manager = _manager()
    initial = manager.create_initial("project-1", _manifest())
    candidate = manager.create_candidate("project-1", initial.version_id, _manifest("stale"))
    intervening = manager.create_candidate("project-1", initial.version_id, _manifest("v2"))
    current = manager.commit(intervening, expected_parent=initial.version_id)

    with pytest.raises(VersionConflictError):
        manager.commit(candidate, expected_parent=initial.version_id)

    assert manager.get_latest("project-1") is current
    assert manager.get_version(candidate.version_id) is None


def test_optimistic_concurrency_rejects_stale_candidate():
    manager = _manager()
    initial = manager.create_initial("project-1", _manifest())
    first = manager.create_candidate("project-1", initial.version_id, _manifest("v2"))
    stale = manager.create_candidate("project-1", initial.version_id, _manifest("other"))

    committed = manager.commit(first, expected_parent=initial.version_id)
    with pytest.raises(VersionConflictError):
        manager.commit(stale, expected_parent=initial.version_id)

    assert manager.get_latest("project-1") is committed


def test_candidate_rejects_missing_parent_and_incomplete_manifest():
    manager = _manager()
    with pytest.raises(VersionNotFoundError, match="parent version"):
        manager.create_candidate("project-1", "missing", _manifest())

    initial = manager.create_initial("project-1", _manifest())
    incomplete = _manifest("v2")
    del incomplete["data_flow"]
    with pytest.raises(ValueError, match="every parent artifact layer"):
        manager.create_candidate("project-1", initial.version_id, incomplete)


def test_candidate_rejects_cross_project_parent():
    manager = _manager()
    initial = manager.create_initial("project-1", _manifest())

    with pytest.raises(ValueError, match="must match its parent"):
        manager.create_candidate("project-2", initial.version_id, _manifest("v2"))


def test_initial_version_cannot_have_a_parent():
    with pytest.raises(ValueError, match="initial version cannot have a parent"):
        _manager().create_initial("project-1", _manifest(), parent_version_id="old-version")
