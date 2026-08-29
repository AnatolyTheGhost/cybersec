"""
Rule to detect Redis passwords and auth connection strings.
"""

from typing import Any

from engine.domain.finding import Finding, FindingKind, Severity
from modules.ast.nodes import SourceRange
from rules.base.rule import BaseRule
from rules.secrets.utils import (
    extract_string,
    iter_literals,
    node_line,
    normalize_value,
    regex_search,
)


class RedisCredentialsRule(BaseRule):
    """
    Rule to detect hardcoded Redis passwords or redis:// auth URIs.
    """

    id = "secrets.redis_credentials"
    name = "Hardcoded Redis Credentials"
    description = "Detects hardcoded Redis password parameters or connection strings."
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

        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            normalized = normalize_value(value)
            if regex_search(r"redis://(?:[^:@]+:[^@]+@|:[^@]+@)", normalized):
                report(literal, "Hardcoded Redis credentials detected in URI.")

        return findings
