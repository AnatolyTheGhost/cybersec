"""
Rule to detect exec() usage.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class ExecRule(BaseRule):
    """
    Rule to detect usage of exec().
    """

    id = "dangerous_api.exec"
    name = "Exec Usage"
    description = "Detects usage of exec() which allows execution of arbitrary code strings."
    severity = Severity.HIGH
    confidence = 0.8

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for exec() usage
        return []
