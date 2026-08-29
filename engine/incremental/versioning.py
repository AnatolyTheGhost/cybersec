"""Immutable project-version model and atomic publication manager."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, TypeAlias
from uuid import uuid4

from .mutations import VersionId

if TYPE_CHECKING:
    from .version_repository import VersionRepository


ProjectId: TypeAlias = str


class VersionNotFoundError(ValueError):
    """Raised when a requested project version does not exist."""


class VersionConflictError(RuntimeError):
    """Raised when optimistic publication detects a changed latest version."""


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    """Immutable reference to one artifact included in a project version."""

    artifact_id: str
    artifact_type: str
    artifact_version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_id, str) or not self.artifact_id.strip():
            raise ValueError("artifact_id is required")
        if not isinstance(self.artifact_type, str) or not self.artifact_type.strip():
            raise ValueError("artifact_type is required")
        if not isinstance(self.artifact_version, int) or self.artifact_version < 1:
            raise ValueError("artifact_version must be a positive integer")


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if isinstance(value, set):
        return frozenset(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ProjectVersion:
    """An immutable, complete manifest of one project's artifact snapshot."""

    project_id: ProjectId
    artifact_manifest: Mapping[str, ArtifactRef]
    parent_version_id: VersionId | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    version_id: VersionId = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    published: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id is required")
        if not isinstance(self.version_id, str) or not self.version_id.strip():
            raise ValueError("version_id is required")
        if self.parent_version_id is not None and (
            not isinstance(self.parent_version_id, str) or not self.parent_version_id.strip()
        ):
            raise ValueError("parent_version_id must be a non-empty string")
        if self.parent_version_id == self.version_id:
            raise ValueError("a version cannot be its own parent")
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")
        if not isinstance(self.artifact_manifest, Mapping):
            raise TypeError("artifact_manifest must be a mapping")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")

        manifest = dict(self.artifact_manifest)
        for artifact_type, artifact_ref in manifest.items():
            if not isinstance(artifact_type, str) or not artifact_type.strip():
                raise ValueError("artifact manifest keys must be non-empty strings")
            if not isinstance(artifact_ref, ArtifactRef):
                raise TypeError("artifact_manifest values must be ArtifactRef instances")
            if artifact_ref.artifact_type != artifact_type:
                raise ValueError("artifact manifest key must match ArtifactRef.artifact_type")

        object.__setattr__(self, "artifact_manifest", MappingProxyType(manifest))
        object.__setattr__(self, "metadata", _freeze(self.metadata))


class VersionManager:
    """Create, query, and atomically publish immutable project versions."""

    def __init__(self, repository: "VersionRepository") -> None:
        self._repository = repository

    def create_initial(
        self,
        project_id: ProjectId,
        artifact_manifest: Mapping[str, ArtifactRef],
        *,
        metadata: Mapping[str, Any] | None = None,
        parent_version_id: VersionId | None = None,
    ) -> ProjectVersion:
        """Create and publish the first version of a project."""

        if parent_version_id is not None:
            raise ValueError("an initial version cannot have a parent")
        if self._repository.get_latest(project_id) is not None:
            raise ValueError("project already has an initial version")

        initial = ProjectVersion(
            project_id=project_id,
            artifact_manifest=artifact_manifest,
            metadata=metadata or {},
            published=True,
        )
        self._repository.store_initial(initial)
        return initial

    def get_version(self, version_id: VersionId) -> ProjectVersion | None:
        """Return a version by its globally unique identifier."""

        return self._repository.get(version_id)

    def get_latest(self, project_id: ProjectId) -> ProjectVersion | None:
        """Return the latest published version for a project."""

        return self._repository.get_latest(project_id)

    def get_artifact_references(self, version_id: VersionId) -> Mapping[str, ArtifactRef]:
        """Return the immutable manifest for a published or candidate version."""

        version = self.get_version(version_id)
        if version is None:
            raise VersionNotFoundError(f"version {version_id!r} does not exist")
        return version.artifact_manifest

    def create_candidate(
        self,
        project_id: ProjectId,
        parent_version_id: VersionId,
        artifact_manifest: Mapping[str, ArtifactRef],
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> ProjectVersion:
        """Create an unpublished complete snapshot based on one parent version."""

        parent = self.get_version(parent_version_id)
        if parent is None:
            raise VersionNotFoundError(f"parent version {parent_version_id!r} does not exist")
        if parent.project_id != project_id:
            raise ValueError("candidate project_id must match its parent version")
        if set(artifact_manifest) != set(parent.artifact_manifest):
            raise ValueError("candidate artifact_manifest must contain every parent artifact layer")

        return ProjectVersion(
            project_id=project_id,
            parent_version_id=parent.version_id,
            artifact_manifest=artifact_manifest,
            metadata=metadata or {},
        )

    def commit(self, candidate: ProjectVersion, *, expected_parent: VersionId) -> ProjectVersion:
        """Atomically publish a candidate if its parent is still latest.

        The repository performs the check and publication under one lock, so a
        failed optimistic-concurrency check leaves the latest version intact.
        """

        if not isinstance(candidate, ProjectVersion):
            raise TypeError("candidate must be a ProjectVersion")
        if candidate.published:
            raise ValueError("candidate is already published")
        if candidate.parent_version_id != expected_parent:
            raise ValueError("candidate parent_version_id must match expected_parent")

        return self._repository.publish(candidate, expected_parent=expected_parent)

    def get_lineage(self, version_id: VersionId) -> tuple[ProjectVersion, ...]:
        """Return the version and its ancestors, from child to initial version."""

        version = self.get_version(version_id)
        if version is None:
            raise VersionNotFoundError(f"version {version_id!r} does not exist")

        lineage = []
        while version is not None:
            lineage.append(version)
            version = self.get_version(version.parent_version_id) if version.parent_version_id else None
        return tuple(lineage)
