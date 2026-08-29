"""
mutations_receiver/scan.py
==========================
Public entry point for triggering a full repository scan through the
Receiver → Server pipeline.

Usage
-----
    from mutations_receiver import scan_repository, ScanResult, ScanError

    result = scan_repository(
        repository_path="/path/to/repo",
        goal="detect injection vulnerabilities",
    )
    for finding in result.findings:
        print(finding.severity, finding.rule_id, finding.message)

Design notes
------------
- ``workspace_id`` is derived as a SHA-1 hex of the *absolute* path so
  repeated calls for the same repository reuse the same server-side context
  without requiring the caller to manage an id.
- ``goal`` (singular) is wrapped into ``[goal]`` before forwarding to
  ``start_analysis()``, which accepts a list for future multi-goal support.
- Network or server errors are re-raised as ``ScanError`` so callers never
  need to catch raw ``RuntimeError`` or ``urllib.error`` exceptions.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Any

from .backend_client import BackendClient


# ---------------------------------------------------------------------------
# Typed response models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SourceRangeResult:
    """Deserialised location of a finding within a source file."""
    file: str
    start_line: int
    end_line: int
    start_col: int | None
    end_col: int | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SourceRangeResult":
        return cls(
            file=data.get("file", ""),
            start_line=data.get("start_line", 1),
            end_line=data.get("end_line", 1),
            start_col=data.get("start_col"),
            end_col=data.get("end_col"),
        )


@dataclass(frozen=True)
class FindingResult:
    """
    Deserialised canonical Finding as returned by the analysis server.

    Field names mirror ``engine.domain.finding.Finding.to_dict()`` so the
    structure is a 1-to-1 round-trip of the server contract.
    """
    id: str
    kind: str
    severity: str
    severity_rank: int
    location: SourceRangeResult
    rule_id: str
    confidence: float
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FindingResult":
        return cls(
            id=data.get("id", ""),
            kind=data.get("kind", "unknown"),
            severity=data.get("severity", "INFO"),
            severity_rank=data.get("severity_rank", 0),
            location=SourceRangeResult.from_dict(data.get("location", {})),
            rule_id=data.get("rule_id", ""),
            confidence=data.get("confidence", 0.0),
            message=data.get("message", ""),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True)
class ScanResult:
    """
    Typed result returned by ``scan_repository()``.

    Attributes
    ----------
    workspace_id:
        Stable identifier derived from the repository path.
    workspace_path:
        Absolute path to the scanned repository, echoed from the server.
    goal:
        The analysis goal that was passed to the scan.
    status:
        Server-reported scan status (e.g. ``"queued"``).
    finding_count:
        Number of findings in ``findings`` (convenience mirror of ``len(findings)``).
    findings:
        Ordered list of canonical findings produced by the engine.
    raw_response:
        The full server response dict for debugging / forward-compatibility.
    """
    workspace_id: str
    workspace_path: str
    goal: str
    status: str
    finding_count: int
    findings: tuple[FindingResult, ...]
    raw_response: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_response(
        cls,
        response: dict[str, Any],
        *,
        workspace_id: str,
        goal: str,
    ) -> "ScanResult":
        raw_findings = response.get("findings", [])
        findings = tuple(FindingResult.from_dict(f) for f in raw_findings)
        return cls(
            workspace_id=workspace_id,
            workspace_path=response.get("workspace_path", ""),
            goal=goal,
            status=response.get("status", ""),
            finding_count=len(findings),
            findings=findings,
            raw_response=response,
        )


# ---------------------------------------------------------------------------
# Error type
# ---------------------------------------------------------------------------

class ScanError(RuntimeError):
    """
    Raised when ``scan_repository()`` cannot reach the server or the server
    returns an error response.

    The original exception (``RuntimeError`` from ``BackendClient``) is
    chained as ``__cause__`` for full traceback visibility.
    """


# ---------------------------------------------------------------------------
# Workspace id derivation
# ---------------------------------------------------------------------------

def _derive_workspace_id(repository_path: str) -> str:
    """
    Return a deterministic, stable workspace identifier for *repository_path*.

    Strategy: SHA-1 hex digest of the UTF-8 encoded absolute path.
    SHA-1 is used for compactness only; there is no security requirement here.
    The prefix ``repo-`` distinguishes repository workspace ids from other ids
    that may appear in the server.
    """
    abs_path = os.path.abspath(repository_path)
    digest = hashlib.sha1(abs_path.encode("utf-8")).hexdigest()
    return f"repo-{digest}"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def scan_repository(
    repository_path: str,
    goal: str,
    *,
    server_url: str = "http://127.0.0.1:8000",
) -> ScanResult:
    """
    Trigger a full analysis of a local repository and return the findings.

    Parameters
    ----------
    repository_path:
        Absolute or relative path to the repository root.  Relative paths
        are resolved against the current working directory.
    goal:
        Human-readable description of the analysis objective, e.g.
        ``"detect injection vulnerabilities"`` or ``"find hardcoded secrets"``.
    server_url:
        Base URL of the Cybersec Analysis Server.  Defaults to the local
        development server at ``http://127.0.0.1:8000``.

    Returns
    -------
    ScanResult
        Typed result containing the ordered list of canonical ``FindingResult``
        objects produced by the engine.

    Raises
    ------
    ScanError
        If the server cannot be reached or returns an error response.
    ValueError
        If ``repository_path`` is an empty string.

    Examples
    --------
    >>> result = scan_repository("/path/to/repo", goal="security audit")
    >>> print(f"Found {result.finding_count} issues")
    """
    if not repository_path.strip():
        raise ValueError("repository_path must not be empty")
    if not goal.strip():
        raise ValueError("goal must not be empty")

    abs_path = os.path.abspath(repository_path)
    workspace_id = _derive_workspace_id(abs_path)

    client = BackendClient(base_url=server_url)

    try:
        response = client.start_analysis(
            workspace_id=workspace_id,
            workspace_path=abs_path,
            goals=[goal],
        )
    except RuntimeError as exc:
        raise ScanError(
            f"scan_repository failed for {abs_path!r}: {exc}"
        ) from exc

    return ScanResult.from_response(response, workspace_id=workspace_id, goal=goal)
