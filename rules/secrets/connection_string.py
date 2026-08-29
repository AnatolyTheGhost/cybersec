"""
Rule to detect generic connection strings with embedded passwords.
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


class ConnectionStringRule(BaseRule):
    """
    Rule to detect connection strings containing passwords or security tokens.
    """

    id = "secrets.connection_string"
    name = "Hardcoded Connection String"
    description = "Detects connection strings with embedded username and password credentials."
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

        pattern = r"\b(?:[a-zA-Z0-9]+://[^\s]*(?:@|password=)[^\s]*)\b"
        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            value = normalize_value(value)
            if regex_search(pattern, value):
                report(literal, "Connection string containing embedded credentials detected.")

        for assignment in iter_assignments(semantic_ast):
            value = extract_string(assignment.value) if assignment.value is not None else None
            if not value:
                continue
            for target in assignment.targets:
                target_name = get_target_name(target)
                if target_name and any(token in target_name for token in ["connection_string", "db_url", "database_url", "connection_uri"]):
                    report(assignment, "Hardcoded connection string detected in assignment.")
                    break

        return findings
