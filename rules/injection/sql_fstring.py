"""
Rule to detect SQL injection via Python f-strings.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class SqlFstringRule(BaseRule):
    """
    Rule to detect SQL query formatting via formatted string literals (f-strings).
    """

    id = "injection.sql_fstring"
    name = "SQL Injection via F-String"
    description = "Detects dynamic SQL query construction using python f-strings."
    severity = Severity.HIGH
    confidence = 0.85

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for SQL f-strings
        return []
