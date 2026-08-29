"""
Rule to detect endpoints or operations missing authentication.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class MissingAuthenticationRule(BaseRule):
    """
    Rule to detect endpoints lacking authentication decorators or guards.
    """

    id = "authorization.missing_authentication"
    name = "Missing Authentication"
    description = "Detects sensitive API routes or endpoints missing authentication requirements."
    severity = Severity.HIGH
    confidence = 0.8

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for missing authentication
        return []
