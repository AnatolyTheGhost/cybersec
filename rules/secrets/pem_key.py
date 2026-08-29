"""
Rule to detect PEM-encoded private keys or certificates containing secrets.
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


class PemKeyRule(BaseRule):
    """
    Rule to detect PEM formatted key blocks in source files.
    """

    id = "secrets.pem_key"
    name = "Embedded PEM Key"
    description = "Detects PEM-formatted key blocks embedded in code."
    severity = Severity.HIGH
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

        regex = r"-----BEGIN [A-Z ]*KEY-----.*-----END [A-Z ]*KEY-----"
        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            if regex_search(regex, normalize_value(value)):
                report(literal, "Embedded PEM-formatted key block detected.")

        return findings
