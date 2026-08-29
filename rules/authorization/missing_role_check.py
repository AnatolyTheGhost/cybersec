"""
Rule to detect operations missing role checks.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class MissingRoleCheckRule(BaseRule):
    """
    Rule to detect endpoints that fail to verify user roles before execution.
    """

    id = "authorization.missing_role_check"
    name = "Missing Role Check"
    description = "Detects role-restricted operations executing without verifying user roles."
    severity = Severity.HIGH
    confidence = 0.75

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for missing role checks
        return []
