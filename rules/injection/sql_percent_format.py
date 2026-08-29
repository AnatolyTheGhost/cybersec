"""
Rule to detect SQL injection via percent (%) string formatting.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class SqlPercentFormatRule(BaseRule):
    """
    Rule to detect SQL query construction using % formatting.
    """

    id = "injection.sql_percent_format"
    name = "SQL Injection via Percent Formatting"
    description = "Detects dynamic SQL query construction using % operator formatting."
    severity = Severity.HIGH
    confidence = 0.85

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for SQL percent formatting
        return []
