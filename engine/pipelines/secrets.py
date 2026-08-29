"""
Secrets Analysis Pipeline.

Fixed execution order:
Repository -> AST -> Semantic AST -> Secrets Rule Pack -> Findings
"""

import logging
from typing import Any, List

from engine.pipelines.base import BasePipeline
from rules.base.finding import Finding
from rules.base.package import RulePackage
from rules.secrets.package import PACKAGE as SECRETS_PACKAGE
from engine.context import AnalysisContext

logger = logging.getLogger(__name__)


class SecretsPipeline(BasePipeline):

    def execute(
        self,
        workspace_path: str,
        context: AnalysisContext,
        rule_package: RulePackage = SECRETS_PACKAGE,
        
    ) -> list[Finding]:

        logger.info("Executing SecretsPipeline on %s", workspace_path)

        # 1. Построить AST
        ast = self.ast_builder.build(
            source_code=context.source_code,
            workspace_path=context.workspace_path,
        )

        # 2. Построить Semantic AST
        semantic_ast = self.semantic_builder.build(ast)

        # 3. Сохранить артефакт в контексте
        context.semantic_ast = semantic_ast

        # 4. Запустить правила
        findings = []

        for rule_cls in rule_package.rules:
            rule = rule_cls()
            findings.extend(rule.analyze(context))

        return findings