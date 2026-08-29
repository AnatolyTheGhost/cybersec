"""
engine/domain/
==============
Canonical output contract of the analysis engine.

All types exported here form the public Finding API consumed by the API tier
and any future enrichment subsystems.
"""

from engine.domain.finding import (
    Finding,
    SourceRange,
    Severity,
    FindingKind,
)

__all__ = [
    "Finding",
    "SourceRange",
    "Severity",
    "FindingKind",
]
