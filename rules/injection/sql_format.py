"""
Rule to detect SQL injection via str.format().
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class SqlFormatRule(BaseRule):
    """
    Rule to detect SQL query construction using str.format().
    """

    id = "injection.sql_format"
    name = "SQL Injection via str.format()"
    description = "Detects dynamic SQL query construction using str.format()."
    severity = Severity.HIGH
    confidence = 0.85

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for SQL str.format()
        return []
