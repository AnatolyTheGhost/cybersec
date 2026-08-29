"""
engine/
=======
The canonical, refactored analysis engine.

Layer responsibilities
----------------------
config_engine.py        →  declarative config objects (immutable, validated)
engine/registry.py      →  mode registry (injectable, testable)
engine/findings.py      →  legacy Finding model (internal rule output)
engine/domain/          →  canonical Finding contract (API output)
engine/mapping/         →  mapping layer (legacy → domain)
engine/context.py       →  AnalysisContext (inter-layer data carrier)
engine/rule_engine.py   →  Rule ABC + RuleEngine (execution only)
engine/orchestrator.py  →  Orchestrator / pipeline (control flow only)
engine/rules/           →  concrete Rule implementations
"""

# from engine.findings import Finding, FindingFilter
from engine.context import AnalysisContext
from engine.domain.finding import (
    Finding as DomainFinding,
    SourceRange,
    Severity,
    FindingKind,
)

__all__ = [
    # "Finding",
    # "FindingFilter",
    "DomainFinding",
    "SourceRange",
    "Severity",
    "FindingKind",
    "AnalysisContext",
]
