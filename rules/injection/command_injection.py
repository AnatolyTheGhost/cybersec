"""
Rule to detect command injection vulnerabilities.
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class CommandInjectionRule(BaseRule):
    """
    Rule to detect OS command injection vulnerabilities.
    """

    id = "injection.command_injection"
    name = "Command Injection"
    description = "Detects unsanitized input passed to system commands, os.system, or popen."
    severity = Severity.CRITICAL
    confidence = 0.9

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for command injection
        return []
