"""
Artifacts API Endpoint Module.

Provides FastAPI endpoints for fetching and uploading code analysis artifacts.

Responsibility:
- HTTP request validation for artifact payload uploads.
- Response serialization.
- Calling ArtifactService.

No business logic allowed here.

TODO:
- Support binary payload upload and version comparison endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from models.schemas import ArtifactResponse, ArtifactSaveRequest
from services.artifact_service import ArtifactService

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

_artifact_service = ArtifactService()


def get_artifact_service() -> ArtifactService:
    """Dependency injector for ArtifactService."""
    return _artifact_service


@router.post("", response_model=ArtifactResponse)
def save_artifact(
    request: ArtifactSaveRequest,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactResponse:
    """
    Save a new version of an analysis artifact.

    TODO: Stream large payload uploads directly to storage backend.
    """
    version = service.save_artifact(
        repository_id=request.repository_id,
        artifact_type=request.artifact_type,
        data=request.data,
        artifact_hash=request.artifact_hash,
    )
    return ArtifactResponse(
        version_id=version.version_id,
        artifact_type=version.artifact_type,
        artifact_hash=version.artifact_hash,
        parent_version_id=version.parent_version_id,
        created_at=version.created_at,
        data=version.data,
    )


@router.get("/{repository_id}/{artifact_type}", response_model=ArtifactResponse)
def get_latest_artifact(
    repository_id: str,
    artifact_type: str,
    service: ArtifactService = Depends(get_artifact_service),
) -> ArtifactResponse:
    """
    Get latest version of a specific artifact type for a repository.

    TODO: Return empty payload metadata if no version exists yet.
    """
    version = service.get_latest_artifact(repository_id, artifact_type)
    if version is None:
        raise HTTPException(
            status_code=404,
            detail=f"No artifact found for repository {repository_id} and type {artifact_type}",
        )
    return ArtifactResponse(
        version_id=version.version_id,
        artifact_type=version.artifact_type,
        artifact_hash=version.artifact_hash,
        parent_version_id=version.parent_version_id,
        created_at=version.created_at,
        data=version.data,
    )
