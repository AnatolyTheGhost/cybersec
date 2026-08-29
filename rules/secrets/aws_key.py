"""
Rule to detect AWS Access Key / Secret Key leaks.
"""

from typing import Any

from engine.domain.finding import Finding, FindingKind, Severity
from modules.ast.nodes import SourceRange
from rules.base.rule import BaseRule
from rules.secrets.utils import (
    extract_string,
    get_target_name,
    iter_assignments,
    iter_literals,
    node_line,
    normalize_value,
    regex_search,
)


class AwsKeyRule(BaseRule):
    """
    Rule to detect hardcoded AWS API keys and secrets.
    """

    id = "secrets.aws_key"
    name = "Hardcoded AWS Key"
    description = "Detects hardcoded AWS Access Key IDs or Secret Access Keys."
    severity = Severity.CRITICAL
    confidence = 0.9

    def analyze(self, context: Any) -> list[Finding]:
        findings: list[Finding] = []
        semantic_ast = getattr(context, "semantic_ast", None)
        if semantic_ast is None:
            return findings

        seen: set[tuple[int, str]] = set()

        def report(node, message: str):
            line = node_line(node)
            key = (line, message)
            if key not in seen:
                seen.add(key)
                findings.append(
                    Finding(
                        id=Finding.generate_id(),
                        kind=FindingKind.HARDCODED_SECRET,
                        severity=self.severity,
                        location=SourceRange(
                            file=context.workspace_path,
                            start_line=line,
                            start_column=0,
                            end_line=line,
                            end_column=0,
                        ),
                        rule_id=self.id,
                        confidence=self.confidence,
                        message=message,
                    )
                )

        for assignment in iter_assignments(semantic_ast):
            value = extract_string(assignment.value) if assignment.value is not None else None
            if not value:
                continue
            value = normalize_value(value)
            for target in assignment.targets:
                target_name = get_target_name(target)
                if not target_name:
                    continue
                if "access_key_id" in target_name or "aws_access_key" in target_name:
                    if value.startswith(("AKIA", "ASIA", "ANPA", "AGPA", "AIDA", "AROA", "ACCA")) and len(value) == 20 and value.isalnum():
                        report(assignment, "Hardcoded AWS Access Key ID detected.")
                if "secret_access_key" in target_name or "aws_secret" in target_name:
                    if len(value) >= 8:
                        report(assignment, "Hardcoded AWS Secret Access Key detected.")

        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            value = normalize_value(value)
            if regex_search(r"\b(AKIA|ASIA|ANPA|AGPA|AIDA|AROA|ACCA)[A-Z0-9]{16}\b", value):
                report(literal, "Potential hardcoded AWS Access Key ID detected.")
            if regex_search(r"\b[A-Za-z0-9/+=]{40}\b", value) and any(keyword in value.lower() for keyword in ["aws", "secret"]):
                report(literal, "Potential hardcoded AWS Secret Access Key detected.")

        return findings
