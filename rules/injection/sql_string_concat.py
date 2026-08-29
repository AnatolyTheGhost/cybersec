"""
Rule to detect SQL injection via string concatenation.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class SqlStringConcatRule(BaseRule):
    """
    Rule to detect SQL query construction via string concatenation (+ operator).
    """

    id = "injection.sql_string_concat"
    name = "SQL Injection via String Concatenation"
    description = "Detects dynamic SQL query construction using string concatenation."
    severity = Severity.HIGH
    confidence = 0.85

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for SQL string concatenation
        return []
