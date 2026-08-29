from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalysisPack(str, Enum):
    """
    Analysis pack identifier for pipeline dispatching.
    """
    DANGEROUS_API = "dangerous_api"
    SECRETS = "secrets"
    INJECTION = "injection"
    AUTHORIZATION = "authorization"


class SessionStartRequest(BaseModel):
    workspace_id: str
    workspace_path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SessionEndRequest(BaseModel):
    session_id: str


class SessionResponse(BaseModel):
    id: str
    workspace_id: str
    workspace_path: str
    created_at: datetime
    ended_at: Optional[datetime] = None
    status: str
    metadata: Dict[str, Any]


class ScanStartRequest(BaseModel):
    # workspace_id: str
    workspace_path: str
    source_code: str
    # goals: List[str] = Field(
    #     default_factory=list,
    #     description="Target goal or rule set identifiers for scan execution",
    # )
    pack: Optional[AnalysisPack] = Field(
        default=None,
        description="AnalysisPack enum or identifier to dispatch directly to deterministic pipeline",
    )


class ScanMutationRequest(BaseModel):
    workspace_id: str
    mutations: List[Dict[str, Any]] = Field(default_factory=list)

class Position(BaseModel):
    line: int
    column: int


class FindingLocation(BaseModel):
    file: str
    start: Position
    end: Position

class FindingResponse(BaseModel):
    id: str
    kind: str
    severity: str
    severity_rank: int
    location: FindingLocation
    rule_id: str
    confidence: float
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScanResponse(BaseModel):
    # workspace_id: str = ""
    workspace_path: str = ""
    # goals: List[str] = Field(default_factory=list)
    # command: str = ""
    status: str
    mutations: int = 0
    findings: List[FindingResponse]
    finding_count: int


class RepositoryCreateRequest(BaseModel):
    workspace_path: str
    name: str


class RepositoryResponse(BaseModel):
    repository_id: str
    name: str
    workspace_path: str
    status: str


class ArtifactSaveRequest(BaseModel):
    repository_id: str
    artifact_type: str
    artifact_hash: str
    data: Any


class ArtifactResponse(BaseModel):
    version_id: str
    artifact_type: str
    artifact_hash: str
    parent_version_id: Optional[str] = None
    created_at: datetime
    data: Any


class FindingResponse(BaseModel):
    scan_id: str
    findings: List[Dict[str, Any]]
    count: int
