"""
Rule to detect SMTP mail server credentials.
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


class SmtpCredentialsRule(BaseRule):
    """
    Rule to detect hardcoded SMTP usernames and passwords.
    """

    id = "secrets.smtp_credentials"
    name = "Hardcoded SMTP Credentials"
    description = "Detects hardcoded SMTP server credentials in source code."
    severity = Severity.HIGH
    confidence = 0.85

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
            target_names = [get_target_name(target) for target in assignment.targets if get_target_name(target)]
            value = extract_string(assignment.value) if assignment.value is not None else None
            if not value or not target_names:
                continue
            if any("smtp" in name for name in target_names) and any(token in name for name in target_names for token in ["pass", "password", "secret"]):
                report(assignment, "Hardcoded SMTP credential detected.")

        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            normalized = normalize_value(value)
            if regex_search(r"smtp://(?:[^:@]+:[^@]+@|:[^@]+@)", normalized):
                report(literal, "Hardcoded SMTP credentials detected in URI.")

        return findings
