"""
Rule to detect unsafe tempfile.mktemp usage.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class TempfileMktempRule(BaseRule):
    """
    Rule to detect tempfile.mktemp() usage.
    """

    id = "dangerous_api.tempfile_mktemp"
    name = "Unsafe Tempfile Mktemp"
    description = "Detects tempfile.mktemp() which is vulnerable to Race Conditions (TOCTOU)."
    severity = Severity.MEDIUM
    confidence = 0.95

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for tempfile.mktemp()
        return []
