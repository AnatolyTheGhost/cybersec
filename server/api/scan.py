from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from engine.context import AnalysisContext

print(AnalysisContext)
print(AnalysisContext.__module__)
print(AnalysisContext.__annotations__)

from engine.pipelines.authorization import AuthorizationPipeline
from engine.pipelines.base import BasePipeline
from engine.pipelines.dangerous_api import DangerousApiPipeline
from engine.pipelines.injection import InjectionPipeline
from engine.pipelines.secrets import SecretsPipeline

from models.schemas import AnalysisPack, ScanStartRequest, ScanResponse

from rules.authorization.package import PACKAGE as AUTHORIZATION_PACKAGE
from rules.dangerous_api.package import PACKAGE as DANGEROUS_API_PACKAGE
from rules.injection.package import PACKAGE as INJECTION_PACKAGE
from rules.secrets.package import PACKAGE as SECRETS_PACKAGE


router = APIRouter(prefix="/scan", tags=["scan"])


_PIPELINE_MAP: Dict[AnalysisPack, tuple[type[BasePipeline], Any]] = {
    AnalysisPack.DANGEROUS_API: (DangerousApiPipeline, DANGEROUS_API_PACKAGE),
    AnalysisPack.SECRETS: (SecretsPipeline, SECRETS_PACKAGE),
    AnalysisPack.INJECTION: (InjectionPipeline, INJECTION_PACKAGE),
    AnalysisPack.AUTHORIZATION: (AuthorizationPipeline, AUTHORIZATION_PACKAGE),
}


@router.post("", response_model=ScanResponse)
def scan(request: ScanStartRequest) -> ScanResponse:
    pipeline_entry = _PIPELINE_MAP.get(request.pack)

    if pipeline_entry is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported analysis pack: {request.pack}",
        )

    pipeline_cls, rule_package = pipeline_entry

    context = AnalysisContext(
        source_code=request.source_code,
        workspace_path=request.workspace_path,
    )

    pipeline = pipeline_cls()

    findings = pipeline.execute(
        workspace_path=request.workspace_path,
        rule_package=rule_package,
        context=context,
    )

    findings = [
        finding.to_dict() if hasattr(finding, "to_dict") else dict(finding)
        for finding in findings
    ]

    return ScanResponse(
        workspace_path=request.workspace_path,
        goals=[request.pack.value] if request.pack is not None else [],
        command="scan",
        findings=findings,
        finding_count=len(findings),
        status="completed",
    )