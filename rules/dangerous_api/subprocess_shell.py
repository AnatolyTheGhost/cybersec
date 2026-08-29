"""
Rule to detect subprocess with shell=True.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class SubprocessShellRule(BaseRule):
    """
    Rule to detect subprocess execution with shell=True.
    """

    id = "dangerous_api.subprocess_shell"
    name = "Subprocess Shell=True Usage"
    description = "Detects subprocess calls using shell=True which can invite shell injection."
    severity = Severity.HIGH
    confidence = 0.9

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for subprocess shell=True
        return []
