"""
Rule to detect hardcoded JWT secret keys.
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


class JwtSecretRule(BaseRule):
    """
    Rule to detect hardcoded JWT signature secrets or public/private keys.
    """

    id = "secrets.jwt_secret"
    name = "Hardcoded JWT Secret"
    description = "Detects hardcoded secret keys used for signing JWT tokens."
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
            value = extract_string(assignment.value) if assignment.value is not None else None
            if not value:
                continue
            for target in assignment.targets:
                target_name = get_target_name(target)
                if target_name and ("jwt_secret" in target_name or "jwt_key" in target_name or "jwt_signing" in target_name):
                    report(assignment, "Hardcoded JWT signing secret detected.")
                    break

        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            if regex_search(r"-----BEGIN (?:RSA )?PRIVATE KEY-----", normalize_value(value)):
                report(literal, "Embedded private key used for JWT signing detected.")

        return findings
