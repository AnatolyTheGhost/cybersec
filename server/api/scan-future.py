"""
Scan API Endpoint Module.

Provides FastAPI endpoints for triggering static analysis scans and handling mutations.
Directly dispatches to deterministic pipelines based on requested AnalysisPack without an intermediate service layer.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from engine.context import AnalysisContext
from engine.pipelines.authorization import AuthorizationPipeline
from engine.pipelines.base import BasePipeline
from engine.pipelines.dangerous_api import DangerousApiPipeline
from engine.pipelines.injection import InjectionPipeline
from engine.pipelines.secrets import SecretsPipeline
from models.schemas import AnalysisPack, ScanMutationRequest, ScanResponse, ScanStartRequest
from rules.authorization.package import PACKAGE as AUTHORIZATION_PACKAGE
from rules.dangerous_api.package import PACKAGE as DANGEROUS_API_PACKAGE
from rules.injection.package import PACKAGE as INJECTION_PACKAGE
from rules.secrets.package import PACKAGE as SECRETS_PACKAGE

router = APIRouter(prefix="/scan", tags=["scan"])

# Session/context management mapping workspace_id -> AnalysisContext
_active_contexts: Dict[str, AnalysisContext] = {}

# Direct pipeline dispatch table
_PIPELINE_MAP: Dict[AnalysisPack, tuple[BasePipeline, Any]] = {
    AnalysisPack.DANGEROUS_API: (DangerousApiPipeline(), DANGEROUS_API_PACKAGE),
    AnalysisPack.SECRETS: (SecretsPipeline(), SECRETS_PACKAGE),
    AnalysisPack.INJECTION: (InjectionPipeline(), INJECTION_PACKAGE),
    AnalysisPack.AUTHORIZATION: (AuthorizationPipeline(), AUTHORIZATION_PACKAGE),
}


def _get_or_create_context(workspace_id: str, workspace_path: str) -> AnalysisContext:
    """Session management helper maintaining analysis contexts per workspace."""
    context = _active_contexts.get(workspace_id)
    if context is None:
        context = AnalysisContext(source_code="", file_path=workspace_path)
        _active_contexts[workspace_id] = context
    return context


@router.post("/start", response_model=ScanResponse)
def start_scan(request: ScanStartRequest) -> ScanResponse:
    """
    Start a static analysis scan by dispatching directly to the corresponding deterministic pipeline.
    """
    context = _get_or_create_context(request.workspace_id, request.workspace_path)
    context.workspace_id = request.workspace_id
    context.workspace_path = request.workspace_path

    # Determine requested pack from request.pack or first match in goals
    pack_choice: AnalysisPack | None = request.pack
    if pack_choice is None:
        for goal in request.goals:
            g_lower = goal.lower()
            if "dangerous" in g_lower:
                pack_choice = AnalysisPack.DANGEROUS_API
                break
            elif "secret" in g_lower:
                pack_choice = AnalysisPack.SECRETS
                break
            elif "inject" in g_lower or "sql" in g_lower:
                pack_choice = AnalysisPack.INJECTION
                break
            elif "auth" in g_lower:
                pack_choice = AnalysisPack.AUTHORIZATION
                break

    # Fallback to DangerousApiPipeline if unspecified
    if pack_choice is None:
        pack_choice = AnalysisPack.DANGEROUS_API

    pipeline_tuple = _PIPELINE_MAP.get(pack_choice)
    if not pipeline_tuple:
        raise HTTPException(status_code=400, detail=f"Unsupported analysis pack: {pack_choice}")

    pipeline, rule_package = pipeline_tuple
    raw_findings = pipeline.execute(
        workspace_path=request.workspace_path,
        rule_package=rule_package,
        context=context,
    )

    findings_dicts: List[Dict[str, Any]] = [
        f.to_dict() if hasattr(f, "to_dict") else dict(f) for f in raw_findings
    ]

    return ScanResponse(
        workspace_id=request.workspace_id,
        workspace_path=request.workspace_path,
        goals=request.goals or [pack_choice.value],
        command="initial",
        status="completed",
        mutations=0,
        findings=findings_dicts,
        finding_count=len(findings_dicts),
    )


@router.post("/mutations", response_model=ScanResponse)
def handle_mutations(request: ScanMutationRequest) -> ScanResponse:
    """
    Handle incremental file modifications and mutations for ongoing analysis.
    Preserves session management and incremental-analysis contracts.
    """
    context = _active_contexts.get(request.workspace_id)
    if context is None:
        raise HTTPException(
            status_code=404,
            detail=f"No active session/context found for workspace {request.workspace_id}",
        )

    # Execute incremental pass on active context
    workspace_path = getattr(context, "workspace_path", "")
    pipeline = DangerousApiPipeline()
    raw_findings = pipeline.execute(
        workspace_path=workspace_path,
        rule_package=DANGEROUS_API_PACKAGE,
        context=context,
    )

    findings_dicts: List[Dict[str, Any]] = [
        f.to_dict() if hasattr(f, "to_dict") else dict(f) for f in raw_findings
    ]

    return ScanResponse(
        workspace_id=request.workspace_id,
        workspace_path=workspace_path,
        goals=getattr(context, "goals", []),
        command="incremental",
        status="completed",
        mutations=len(request.mutations),
        findings=findings_dicts,
        finding_count=len(findings_dicts),
    )
