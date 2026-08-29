"""
Finding data model for rule analysis results.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any

from modules.ast.nodes import SourceRange
from rules.base.severity import Severity


@dataclass(frozen=True)
class Finding:
    """
    Represents a single issue or vulnerability detected by a Rule.

    Attributes
    ----------
    rule_id:
        Unique dot-separated rule identifier.
    message:
        Human-readable description of the finding.
    severity:
        Severity level of the finding (Severity enum or string representation).
    file:
        File path where the issue was detected.
    line:
        1-based line number of the finding.
    confidence:
        Confidence score in [0.0, 1.0].
    cwe:
        Optional CWE identifier.
    owasp:
        Optional OWASP category.
    trace:
        Optional trace of file:line markers.
    metadata:
        Additional contextual metadata dictionary.
    """

    rule_id: str
    message: str
    severity: Severity | str
    file: str | None = None
    line: int | None = None
    location: SourceRange | None = None
    confidence: float = 0.0
    cwe: str | None = None
    owasp: str | None = None
    trace: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.severity, Severity):
            object.__setattr__(self, "severity", self.severity.value)
        
        valid_severities = {s.value for s in Severity}
        if self.severity not in valid_severities:
            raise ValueError(
                f"Invalid severity '{self.severity}'. Valid options: {sorted(valid_severities)}"
            )
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.location is None:
            if self.file is None or self.line is None:
                self.location = SourceRange(file="<unknown>", start_line=1, end_line=1)
            else:
                self.location = SourceRange(file=self.file, start_line=self.line, end_line=self.line)
        else:
            if self.file is None:
                object.__setattr__(self, "file", self.location.file)
            if self.line is None:
                object.__setattr__(self, "line", self.location.start_line)

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary representation of the finding."""
        payload = dataclasses.asdict(self)
        payload["location"] = {
            "file": self.location.file if self.location else self.file or "<unknown>",
            "start": {
                "line": self.location.start_line if self.location else self.line or 1,
                "column": self.location.start_column if self.location else 0,
            },
            "end": {
                "line": self.location.end_line if self.location else self.line or 1,
                "column": self.location.end_column if self.location else 0,
            },
        }
        return payload
