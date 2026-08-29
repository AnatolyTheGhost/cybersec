"""
Rule to detect NoSQL injection vulnerabilities.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class NosqlInjectionRule(BaseRule):
    """
    Rule to detect NoSQL query injection (e.g. MongoDB $where or unescaped query objects).
    """

    id = "injection.nosql_injection"
    name = "NoSQL Injection"
    description = "Detects untrusted input passed to NoSQL query operators."
    severity = Severity.HIGH
    confidence = 0.8

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for NoSQL injection
        return []
