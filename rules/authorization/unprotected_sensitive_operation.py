"""
Rule to detect unprotected sensitive operations.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class UnprotectedSensitiveOperationRule(BaseRule):
    """
    Rule to detect sensitive business logic (e.g. password resets, money transfers) missing verification.
    """

    id = "authorization.unprotected_sensitive_operation"
    name = "Unprotected Sensitive Operation"
    description = "Detects critical state-changing actions executing without re-authentication or token checks."
    severity = Severity.HIGH
    confidence = 0.8

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for unprotected sensitive operations
        return []
