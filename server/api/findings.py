"""
Findings API Endpoint Module.

Provides FastAPI endpoints for querying security findings and vulnerability reports.

Responsibility:
- HTTP request parameter validation.
- Response serialization for finding objects.
- Calling FindingService.

No business logic allowed here.

TODO:
- Add query parameters for filtering findings by severity, rule, and pagination.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from models.schemas import FindingResponse
from services.finding_service import FindingService

router = APIRouter(prefix="/findings", tags=["findings"])

_finding_service = FindingService()


def get_finding_service() -> FindingService:
    """Dependency injector for FindingService."""
    return _finding_service


@router.get("/scan/{scan_id}", response_model=FindingResponse)
def get_findings_for_scan(
    scan_id: str,
    service: FindingService = Depends(get_finding_service),
) -> FindingResponse:
    """
    Retrieve security findings produced by a scan.

    TODO: Support CSV/JSON export formatting and pagination.
    """
    findings = service.get_findings_for_scan(scan_id)
    return FindingResponse(
        scan_id=scan_id,
        findings=findings,
        count=len(findings),
    )
