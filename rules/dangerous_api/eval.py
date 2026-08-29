"""
Rules for dangerous API usage.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class EvalRule(BaseRule):
    """
    Rule to detect usage of the eval() built-in function.
    """

    id = "dangerous_api.eval"
    name = "Eval Usage"
    description = "Detects usage of eval() which can lead to dynamic code execution vulnerabilities."
    severity = Severity.HIGH
    confidence = 0.8

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for eval() usage
        return []
