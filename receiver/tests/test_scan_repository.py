"""
tests/test_scan_repository.py
==============================
Unit tests for the scan_repository() entry point.

All tests use unittest.mock to stub BackendClient so no live server is needed.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mutations_receiver import (
    FindingResult,
    ScanError,
    ScanResult,
    scan_repository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_analysis_response(
    workspace_id: str = "repo-abc",
    workspace_path: str = "/some/repo",
    goals: list[str] | None = None,
    findings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal server AnalysisResponse dict."""
    return {
        "workspace_id": workspace_id,
        "workspace_path": workspace_path,
        "goals": goals or ["security"],
        "command": "initial",
        "status": "queued",
        "mutations": 0,
        "findings": findings or [],
        "finding_count": len(findings or []),
    }


def _make_finding_dict(
    rule_id: str = "injection.sql.raw_query",
    severity: str = "HIGH",
    message: str = "Raw SQL query",
) -> dict[str, Any]:
    """Build a minimal FindingResponse dict matching the server contract."""
    return {
        "id": "test-uuid-1234",
        "kind": "injection",
        "severity": severity,
        "severity_rank": 3,
        "location": {
            "file": "/some/repo/app.py",
            "start_line": 42,
            "end_line": 42,
            "start_col": None,
            "end_col": None,
        },
        "rule_id": rule_id,
        "confidence": 0.9,
        "message": message,
        "metadata": {"cwe": "CWE-89"},
    }


# ---------------------------------------------------------------------------
# Test: payload sent to the server
# ---------------------------------------------------------------------------

class TestScanRepositoryPayload:
    """Verify that scan_repository sends the correct data to BackendClient."""

    def test_sends_correct_path_and_goal(self, tmp_path):
        """workspace_path must be the absolute path; goal must be wrapped in a list."""
        repo = tmp_path / "my_project"
        repo.mkdir()

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            return_value=_make_analysis_response(
                workspace_path=str(repo),
            ),
        ) as mock_start:
            scan_repository(str(repo), goal="find secrets")

        mock_start.assert_called_once()
        _, kwargs = mock_start.call_args
        assert kwargs["workspace_path"] == str(repo)            # workspace_path
        assert kwargs["goals"] == ["find secrets"]     # goals list wraps single goal

    def test_workspace_id_is_derived_from_path(self, tmp_path):
        """workspace_id must be the repo-<sha1> of the absolute path."""
        repo = tmp_path / "project"
        repo.mkdir()
        abs_path = str(repo.resolve())
        expected_id = "repo-" + hashlib.sha1(abs_path.encode("utf-8")).hexdigest()

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            return_value=_make_analysis_response(workspace_id=expected_id),
        ) as mock_start:
            scan_repository(str(repo), goal="security")

        _, kwargs = mock_start.call_args
        assert kwargs["workspace_id"] == expected_id          # workspace_id


# ---------------------------------------------------------------------------
# Test: workspace_id stability
# ---------------------------------------------------------------------------

class TestWorkspaceIdDeterminism:
    """workspace_id must be identical across repeated calls for the same path."""

    def test_same_path_produces_same_workspace_id(self, tmp_path):
        repo = tmp_path / "stable"
        repo.mkdir()
        response = _make_analysis_response()

        ids: list[str] = []

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            return_value=response,
        ) as mock_start:
            scan_repository(str(repo), goal="check")
            scan_repository(str(repo), goal="check")

        for call in mock_start.call_args_list:
            ids.append(call[1]["workspace_id"])

        assert ids[0] == ids[1], "workspace_id must be deterministic for the same path"

    def test_different_paths_produce_different_workspace_ids(self, tmp_path):
        repo_a = tmp_path / "alpha"
        repo_b = tmp_path / "beta"
        repo_a.mkdir()
        repo_b.mkdir()
        response = _make_analysis_response()

        ids: list[str] = []

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            return_value=response,
        ) as mock_start:
            scan_repository(str(repo_a), goal="check")
            scan_repository(str(repo_b), goal="check")

        for call in mock_start.call_args_list:
            ids.append(call[1]["workspace_id"])

        assert ids[0] != ids[1], "Different paths must yield different workspace_ids"


# ---------------------------------------------------------------------------
# Test: structured ScanResult returned
# ---------------------------------------------------------------------------

class TestScanResultDeserialization:
    """scan_repository must return a fully typed ScanResult."""

    def test_empty_findings_returns_zero_count(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            return_value=_make_analysis_response(),
        ):
            result = scan_repository(str(repo), goal="security")

        assert isinstance(result, ScanResult)
        assert result.finding_count == 0
        assert result.findings == ()

    def test_single_finding_is_deserialised_correctly(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        finding_dict = _make_finding_dict(rule_id="injection.sql.raw_query")

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            return_value=_make_analysis_response(findings=[finding_dict]),
        ):
            result = scan_repository(str(repo), goal="find sql injection")

        assert result.finding_count == 1
        f: FindingResult = result.findings[0]
        assert f.rule_id == "injection.sql.raw_query"
        assert f.severity == "HIGH"
        assert f.kind == "injection"
        assert f.confidence == 0.9
        assert f.location.file == "/some/repo/app.py"
        assert f.location.start_line == 42

    def test_multiple_findings_preserved_in_order(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        dicts = [
            _make_finding_dict(rule_id=f"rule.{i}", severity="LOW")
            for i in range(5)
        ]

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            return_value=_make_analysis_response(findings=dicts),
        ):
            result = scan_repository(str(repo), goal="full audit")

        assert result.finding_count == 5
        for i, f in enumerate(result.findings):
            assert f.rule_id == f"rule.{i}"

    def test_goal_and_status_are_propagated(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            return_value=_make_analysis_response(goals=["my goal"]),
        ):
            result = scan_repository(str(repo), goal="my goal")

        assert result.goal == "my goal"
        assert result.status == "queued"


# ---------------------------------------------------------------------------
# Test: error handling
# ---------------------------------------------------------------------------

class TestScanRepositoryErrors:
    """Network and server errors must be wrapped in ScanError."""

    def test_network_failure_raises_scan_error(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            side_effect=RuntimeError("Connection refused"),
        ):
            with pytest.raises(ScanError, match="Connection refused"):
                scan_repository(str(repo), goal="security")

    def test_scan_error_chains_original_exception(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        original = RuntimeError("Backend returned 503")

        with patch(
            "mutations_receiver.scan.BackendClient.start_analysis",
            side_effect=original,
        ):
            with pytest.raises(ScanError) as exc_info:
                scan_repository(str(repo), goal="security")

        assert exc_info.value.__cause__ is original

    def test_empty_path_raises_value_error(self):
        with pytest.raises(ValueError, match="repository_path must not be empty"):
            scan_repository("", goal="security")

    def test_empty_goal_raises_value_error(self, tmp_path):
        repo = tmp_path / "repo"
        repo.mkdir()
        with pytest.raises(ValueError, match="goal must not be empty"):
            scan_repository(str(repo), goal="  ")
