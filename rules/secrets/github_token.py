"""
Rule to detect GitHub Personal Access Tokens and OAuth Tokens.
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


class GithubTokenRule(BaseRule):
    """
    Rule to detect exposed GitHub tokens (ghp_, gho_, ghu_, ghs_, ghr_).
    """

    id = "secrets.github_token"
    name = "Hardcoded GitHub Token"
    description = "Detects hardcoded GitHub personal access tokens and secrets."
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

        regex = r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b"
        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            if regex_search(regex, normalize_value(value)):
                report(literal, "Hardcoded GitHub token detected.")

        return findings
