"""
Rule to detect unsafe marshal deserialization.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class MarshalLoadsRule(BaseRule):
    """
    Rule to detect usage of marshal.loads().
    """

    id = "dangerous_api.marshal_loads"
    name = "Unsafe Marshal Deserialization"
    description = "Detects usage of marshal deserialization which is unsecure for untrusted input."
    severity = Severity.HIGH
    confidence = 0.85

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for marshal.loads()
        return []
