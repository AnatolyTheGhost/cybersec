"""
Rule to detect operations missing owner verification.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class MissingOwnerCheckRule(BaseRule):
    """
    Rule to detect resource access lacking ownership validation.
    """

    id = "authorization.missing_owner_check"
    name = "Missing Owner Check"
    description = "Detects resource lookup or modification without validating user ownership."
    severity = Severity.HIGH
    confidence = 0.75

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for missing owner checks
        return []
