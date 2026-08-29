"""
Rule to detect unsafe reflection access.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class ReflectionRule(BaseRule):
    """
    Rule to detect unsafe reflection attribute manipulation (getattr/setattr).
    """

    id = "dangerous_api.reflection"
    name = "Unsafe Reflection Access"
    description = "Detects getattr/setattr usage with dynamically resolved property names."
    severity = Severity.MEDIUM
    confidence = 0.65

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for unsafe reflection
        return []
