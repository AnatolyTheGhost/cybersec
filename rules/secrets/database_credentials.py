"""
Rule to detect hardcoded database connection credentials.
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


class DatabaseCredentialsRule(BaseRule):
    """
    Rule to detect database username/password assignments and inline auth info.
    """

    id = "secrets.database_credentials"
    name = "Hardcoded Database Credentials"
    description = "Detects hardcoded database credentials such as DB_PASS or inline authentication."
    severity = Severity.CRITICAL
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

        db_password_keywords = ["db_pass", "db_password", "database_password", "db_secret", "sql_password", "mysql_password", "postgres_password"]
        for assignment in iter_assignments(semantic_ast):
            value = extract_string(assignment.value) if assignment.value is not None else None
            if not value:
                continue
            value = normalize_value(value)
            for target in assignment.targets:
                target_name = get_target_name(target)
                if target_name and any(keyword in target_name for keyword in db_password_keywords):
                    report(assignment, "Hardcoded database password detected.")
                    break

        for assignment in iter_assignments(semantic_ast):
            for target in assignment.targets:
                target_name = get_target_name(target)
                if not target_name:
                    continue
                if any(token in target_name for token in ["db_uri", "database_url", "mongo_uri", "connection_string", "connection_uri"]):
                    value = extract_string(assignment.value) if assignment.value is not None else None
                    if value and regex_search(r"mongodb?://|mysql://|postgresql?://", value):
                        report(assignment, "Hardcoded database connection URI detected.")
                        break

        return findings
