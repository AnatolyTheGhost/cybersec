"""
Rule to detect hardcoded passwords.
"""

from typing import Any

from engine.domain.finding import Finding, FindingKind, Severity
from modules.ast.nodes import SourceRange
from rules.base.rule import BaseRule
from rules.secrets.utils import (
    extract_string,
    get_target_name,
    iter_assignments,
    node_line,
    normalize_value,
    regex_search,
)


class HardcodedPasswordRule(BaseRule):
    """
    Rule to detect passwords assigned to variable names like password, passwd, secret, etc.
    """

    id = "secrets.hardcoded_password"
    name = "Hardcoded Password"
    description = "Detects plain-text passwords embedded directly in code or config assignments."
    severity = Severity.HIGH
    confidence = 0.8

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

        keywords = ["password", "passwd", "pwd", "secret", "passphrase"]
        for assignment in iter_assignments(semantic_ast):
            value = extract_string(assignment.value) if assignment.value is not None else None
            if not value:
                continue
            for target in assignment.targets:
                target_name = get_target_name(target)
                if target_name and any(keyword in target_name for keyword in keywords):
                    if len(normalize_value(value)) >= 6:
                        report(assignment, "Hardcoded password detected.")
                        break

        return findings
