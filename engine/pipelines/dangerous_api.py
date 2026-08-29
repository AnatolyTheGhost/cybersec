"""
Dangerous API Analysis Pipeline.

Fixed execution order:
Repository -> AST -> Semantic AST -> Dangerous API Rule Pack -> Findings
"""

import logging
from typing import Any, List

from engine.pipelines.base import BasePipeline
from rules.base.finding import Finding
from rules.base.package import RulePackage
from rules.dangerous_api.package import PACKAGE as DANGEROUS_API_PACKAGE

logger = logging.getLogger(__name__)


class DangerousApiPipeline(BasePipeline):
    """
    Deterministic pipeline for Dangerous API analysis.
    """

    def execute(self, workspace_path: str, rule_package: RulePackage = DANGEROUS_API_PACKAGE, context: Any = None) -> List[Finding]:
        """
        Execute Dangerous API pipeline steps in fixed order.
        """
        logger.info("Executing DangerousApiPipeline on workspace: %s", workspace_path)

        # 1. AST construction
        context.ast = self.ast_builder.build(
            source_code=context.source_code,
            file_path=context.file_path,
        )

        # 2. Semantic AST construction
        context.semantic_ast = self.semantic_builder.build(context.ast)

        # 3. Dangerous API Rule Pack execution
        findings: List[Finding] = []
        for rule_cls in rule_package.rules:
            rule = rule_cls()
            rule_findings = rule.analyze(context)
            findings.extend(rule_findings)

        # 4. Return Findings
        return findings
