"""Persistence boundary for immutable project versions."""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod

from .versioning import ProjectId, ProjectVersion, VersionConflictError


class VersionRepository(ABC):
    """Storage operations required for atomic VersionManager publication."""

    @abstractmethod
    def get(self, version_id: str) -> ProjectVersion | None:
        ...

    @abstractmethod
    def get_latest(self, project_id: ProjectId) -> ProjectVersion | None:
        ...

    @abstractmethod
    def store_initial(self, version: ProjectVersion) -> None:
        ...

    @abstractmethod
    def publish(self, candidate: ProjectVersion, *, expected_parent: str) -> ProjectVersion:
        ...


class InMemoryVersionRepository(VersionRepository):
    """Thread-safe in-memory repository with atomic optimistic publication."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._versions: dict[str, ProjectVersion] = {}
        self._latest_by_project: dict[ProjectId, str] = {}

    def get(self, version_id: str) -> ProjectVersion | None:
        with self._lock:
            return self._versions.get(version_id)

    def get_latest(self, project_id: ProjectId) -> ProjectVersion | None:
        with self._lock:
            version_id = self._latest_by_project.get(project_id)
            return self._versions.get(version_id) if version_id is not None else None

    def store_initial(self, version: ProjectVersion) -> None:
        if not version.published or version.parent_version_id is not None:
            raise ValueError("initial version must be published and parentless")
        with self._lock:
            if version.project_id in self._latest_by_project:
                raise ValueError("project already has an initial version")
            if version.version_id in self._versions:
                raise ValueError("version_id already exists")
            self._versions[version.version_id] = version
            self._latest_by_project[version.project_id] = version.version_id

    def publish(self, candidate: ProjectVersion, *, expected_parent: str) -> ProjectVersion:
        if candidate.published:
            raise ValueError("candidate is already published")
        with self._lock:
            latest_id = self._latest_by_project.get(candidate.project_id)
            if latest_id != expected_parent:
                raise VersionConflictError(
                    f"latest version for project {candidate.project_id!r} is {latest_id!r}, "
                    f"not expected parent {expected_parent!r}"
                )
            if candidate.parent_version_id != expected_parent:
                raise ValueError("candidate parent_version_id must match expected_parent")
            if candidate.version_id in self._versions:
                raise ValueError("version_id already exists")

            published = ProjectVersion(
                project_id=candidate.project_id,
                parent_version_id=candidate.parent_version_id,
                artifact_manifest=candidate.artifact_manifest,
                metadata=candidate.metadata,
                version_id=candidate.version_id,
                created_at=candidate.created_at,
                published=True,
            )
            self._versions[published.version_id] = published
            self._latest_by_project[published.project_id] = published.version_id
            return published
