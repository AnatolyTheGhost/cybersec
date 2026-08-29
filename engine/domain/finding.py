"""
engine/domain/finding.py
========================
Canonical Finding contract — the single, authoritative output model of the
analysis engine.  Independent of API tier (Free / Pro / Enterprise) and of
any specific rule implementation.

Design notes
------------
- ``Finding`` is a frozen dataclass so callers cannot mutate engine output.
- ``SourceRange`` is kept separate so it can be embedded in other future
  domain objects (e.g. evidence spans, LLM context windows).
- ``Severity`` and ``FindingKind`` are plain enums; each carries an integer
  value that enables numeric comparison and stable serialisation.
- ``metadata`` is an open dict for ad-hoc rule-level data that doesn't yet
  have a dedicated field.  Planned fields (CWE, OWASP, remediation, LLM
  explanation, fingerprint) will graduate from here into typed attributes.

Must NOT
--------
- Import from engine.rule_engine, engine.orchestrator, or config_engine.
- Contain any analysis logic.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from modules.ast.nodes import SourceRange


# ---------------------------------------------------------------------------
# Severity
# ---------------------------------------------------------------------------

class Severity(int, Enum):
    """Canonical severity levels, ordered from least to most critical."""
    INFO = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_str(cls, value: str) -> "Severity":
        """
        Parse a severity string produced by legacy Rule definitions.

        Accepted values (case-insensitive):
            ``info``, ``informational``, ``low``, ``medium``, ``high``, ``critical``.
        """
        _LEGACY_MAP = {
            "informational": cls.INFO,
            "info": cls.INFO,
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "high": cls.HIGH,
            "critical": cls.CRITICAL,
        }
        try:
            return _LEGACY_MAP[value.lower()]
        except KeyError:
            raise ValueError(
                f"Unknown severity string {value!r}. "
                f"Valid values: {list(_LEGACY_MAP)}"
            )


# ---------------------------------------------------------------------------
# FindingKind
# ---------------------------------------------------------------------------

class FindingKind(str, Enum):
    """
    Coarse category of a finding, derived from the rule that produced it.

    The string value is stable and safe to serialise / store.  New kinds
    must be added here (never invented in mapping code) so the full taxonomy
    remains auditable in one place.
    """
    # Currently implemented rule families
    INJECTION = "injection"            # SQL / command / code injection
    XSS = "xss"                        # Cross-site scripting
    CSRF = "csrf"                       # Cross-site request forgery
    DESERIALIZATION = "deserialization" # Unsafe deserialization
    HARDCODED_SECRET = "hardcoded_secret"
    SSRF = "ssrf"                       # Server-side request forgery
    PATH_TRAVERSAL = "path_traversal"
    XXE = "xxe"                         # XML external entity

    # Placeholder for rule families not yet categorised
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Finding
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Finding:
    """
    The canonical output unit produced by the analysis engine.

    Every rule result, regardless of the rule family or API tier, must be
    expressed as a ``Finding`` before leaving the engine.

    Attributes
    ----------
    id:
        UUID4 string, globally unique per finding instance.  Generated
        automatically by the mapping layer; callers must not set it.
    kind:
        Coarse category (``FindingKind``).
    severity:
        Assessed severity (``Severity``).
    location:
        Precise source location (``SourceRange``).
    rule_id:
        Fully-qualified rule identifier, e.g. ``injection.sql.raw_query``.
    confidence:
        Value in ``[0.0, 1.0]`` reflecting the rule's certainty.
    message:
        Human-readable description of the issue.
    metadata:
        Open dict for data that does not yet have a dedicated field.
        Planned fields that will graduate here: ``cwe``, ``owasp``,
        ``remediation``, ``evidence``, ``fingerprint``, ``llm_explanation``.
    """

    id: str
    kind: FindingKind
    severity: Severity
    location: SourceRange
    rule_id: str
    confidence: float
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "id": self.id,
            "kind": self.kind.value,
            "severity": self.severity.name,
            "severity_rank": self.severity.value,
            "location": {
                "file": self.location.file,
                "start": {
                    "line": self.location.start_line,
                    "column": self.location.start_column,
                },
                "end": {
                    "line": self.location.end_line,
                    "column": self.location.end_column,
                },
            },
            "rule_id": self.rule_id,
            "confidence": round(self.confidence, 4),
            "message": self.message,
            "metadata": self.metadata,
        }

    @staticmethod
    def generate_id() -> str:
        """Generate a fresh unique id for a new Finding."""
        return str(uuid.uuid4())
