"""
Rule to detect Discord Bot Tokens.
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


class DiscordTokenRule(BaseRule):
    """
    Rule to detect exposed Discord bot tokens and webhooks.
    """

    id = "secrets.discord_token"
    name = "Hardcoded Discord Token"
    description = "Detects hardcoded Discord bot tokens."
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

        discord_pattern = r"^(mfa\.|[A-Za-z0-9_-]{40,100})$"
        for assignment in iter_assignments(semantic_ast):
            for target in assignment.targets:
                target_name = get_target_name(target)
                if not target_name:
                    continue
                if "discord" in target_name or "bot_token" in target_name:
                    value = extract_string(assignment.value) if assignment.value is not None else None
                    if value and len(value.strip()) >= 20:
                        report(assignment, "Potential hardcoded Discord bot token detected.")
                        break

        for literal in iter_literals(semantic_ast):
            value = extract_string(literal)
            if not value:
                continue
            value = normalize_value(value)
            if regex_search(discord_pattern, value):
                if regex_search(r"^mfa\.|^[A-Za-z0-9_-]{40,100}$", value):
                    report(literal, "Potential hardcoded Discord token detected.")

        return findings
