"""
Repositories API Endpoint Module.

Provides FastAPI endpoints for registering and viewing repository workspaces.

Responsibility:
- HTTP request validation for repository registration.
- Response serialization.
- Calling RepositoryService.

No business logic allowed here.

TODO:
- Implement repository listing, update, and deletion endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from models.schemas import RepositoryCreateRequest, RepositoryResponse
from services.repository_service import RepositoryService

router = APIRouter(prefix="/repositories", tags=["repositories"])

_repository_service = RepositoryService()


def get_repository_service() -> RepositoryService:
    """Dependency injector for RepositoryService."""
    return _repository_service


@router.post("", response_model=RepositoryResponse)
def create_repository(
    request: RepositoryCreateRequest,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    """
    Register a new workspace repository.

    TODO: Return full database repository entity.
    """
    result = service.register_repository(
        workspace_path=request.workspace_path,
        name=request.name,
    )
    return RepositoryResponse(**result)


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository(
    repository_id: str,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositoryResponse:
    """
    Get repository info by ID.

    TODO: Retrieve repository details from service.
    """
    repo = service.get_repository(repository_id)
    if repo is None:
        raise HTTPException(status_code=404, detail=f"Repository {repository_id} not found")
    return RepositoryResponse(**repo)
