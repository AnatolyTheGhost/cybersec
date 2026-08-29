"""
Rule to detect hardcoded OAuth Client Credentials and Access Tokens.
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


class OauthTokenRule(BaseRule):
    """
    Rule to detect hardcoded OAuth client secrets or access tokens.
    """

    id = "secrets.oauth_token"
    name = "Hardcoded OAuth Secret / Token"
    description = "Detects hardcoded OAuth2 client secrets or access tokens."
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

        oauth_keywords = ["oauth", "oauth_token", "oauth_secret", "client_secret"]
        for assignment in iter_assignments(semantic_ast):
            value = extract_string(assignment.value) if assignment.value is not None else None
            if not value:
                continue
            normalized_value = normalize_value(value)
            for target in assignment.targets:
                target_name = get_target_name(target)
                if target_name and any(keyword in target_name for keyword in oauth_keywords):
                    report(assignment, "Hardcoded OAuth token or secret detected.")
                    break
            if regex_search(r"^(ya29\.|oauth|ya29\.)[A-Za-z0-9_\-\.]{20,}$", normalized_value):
                report(assignment, "Potential hardcoded OAuth access token detected.")

        return findings
