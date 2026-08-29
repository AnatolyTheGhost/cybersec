"""
Rule to detect Azure Client Secret / Key leaks.
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


class AzureKeyRule(BaseRule):
    """
    Rule to detect hardcoded Azure API keys and access tokens.
    """

    id = "secrets.azure_key"
    name = "Hardcoded Azure Key"
    description = "Detects hardcoded Azure secrets, client credentials, or storage keys."
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

        azure_var_keywords = ["azure_client_secret", "azure_storage_key", "azure_secret", "azure_key", "azure_api_key", "azure_access_token"]

        for assignment in iter_assignments(semantic_ast):
            value = extract_string(assignment.value) if assignment.value is not None else None
            if not value:
                continue
            value = normalize_value(value)
            for target in assignment.targets:
                target_name = get_target_name(target)
                if not target_name:
                    continue
                if any(keyword in target_name for keyword in azure_var_keywords):
                    report(assignment, "Hardcoded Azure secret or access key detected.")
                    break

        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            if regex_search(r"\bazure[^\s'\"]*(secret|key|token)[^\s'\"]*\b", value):
                report(literal, "Hardcoded Azure secret-like string detected.")

        return findings
