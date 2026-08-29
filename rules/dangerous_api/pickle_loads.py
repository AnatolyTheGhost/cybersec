"""
Rule to detect unsafe pickle deserialization.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class PickleLoadsRule(BaseRule):
    """
    Rule to detect unsafe pickle.loads() / load() usage.
    """

    id = "dangerous_api.pickle_loads"
    name = "Unsafe Pickle Deserialization"
    description = "Detects usage of pickle deserialization which is vulnerable to arbitrary code execution."
    severity = Severity.CRITICAL
    confidence = 0.9

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for pickle deserialization
        return []
