"""
Rule to detect Insecure Direct Object Reference (IDOR) vulnerabilities.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class IdorRule(BaseRule):
    """
    Rule to detect IDOR flaws where object IDs are accessed directly from client parameters.
    """

    id = "authorization.idor"
    name = "Insecure Direct Object Reference (IDOR)"
    description = "Detects direct object reference lookups without user context validation."
    severity = Severity.HIGH
    confidence = 0.8

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for IDOR vulnerabilities
        return []
