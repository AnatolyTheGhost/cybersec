"""
Rule to detect committed .env files or hardcoded dotenv loading.
"""

from typing import Any

from engine.domain.finding import Finding, FindingKind, Severity
from modules.ast.nodes import SourceRange
from rules.base.rule import BaseRule
from rules.secrets.utils import (
    extract_string,
    get_target_name,
    iter_literals,
    iter_assignments,
    node_line,
    normalize_value,
    regex_search,
)


class DotenvFileRule(BaseRule):
    """
    Rule to detect committed .env files or unhandled dotenv configurations.
    """

    id = "secrets.dotenv_file"
    name = "Committed Dotenv File"
    description = "Detects committed .env configuration files containing environment secrets."
    severity = Severity.HIGH
    confidence = 0.95

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

        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            value = normalize_value(value)
            if value == ".env" or value.endswith("/.env") or value.endswith(".env"):
                report(literal, "Hardcoded dotenv file path detected.")

        for assignment in iter_assignments(semantic_ast):
            for target in assignment.targets:
                target_name = get_target_name(target) if hasattr(target, 'name') else None
                if target_name and "dotenv" in target_name:
                    report(assignment, "Dotenv configuration variable detected.")
                    break

        return findings
