"""
Rule to detect unsafe PyYAML load().
"""

from typing import Any

from rules.base.finding import Finding
from rules.base.rule import BaseRule
from rules.base.severity import Severity


class YamlLoadRule(BaseRule):
    """
    Rule to detect unsafe yaml.load() usage.
    """

    id = "dangerous_api.yaml_load"
    name = "Unsafe YAML Load"
    description = "Detects yaml.load() without SafeLoader which can result in arbitrary object instantiation."
    severity = Severity.HIGH
    confidence = 0.85

    def analyze(self, context: Any) -> list[Finding]:
        # TODO: Implement detection logic for unsafe yaml.load()
        return []
