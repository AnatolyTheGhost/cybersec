"""
Injection Vulnerability Analysis Pipeline.

Fixed execution order:
Repository -> AST -> Semantic AST -> CFG -> Data Flow -> Interprocedural Analysis -> Injection Rule Pack -> Findings
"""

import logging
from typing import Any, List

from engine.pipelines.base import BasePipeline
from rules.base.finding import Finding
from rules.base.package import RulePackage
from rules.injection.package import PACKAGE as INJECTION_PACKAGE

logger = logging.getLogger(__name__)


class InjectionPipeline(BasePipeline):
    """
    Deterministic pipeline for Injection analysis.

    Execution order:
    Source -> AST -> Semantic AST -> CFG -> Data Flow ->
    Interprocedural Analysis -> Rule Pack -> Findings
    """

    def execute(
        self,
        workspace_path: str,
        rule_package: RulePackage = INJECTION_PACKAGE,
        context: Any = None,
    ) -> List[Finding]:

        logger.info("Executing InjectionPipeline on workspace: %s", workspace_path)

        # 1. AST construction
        context.ast = self.ast_builder.build(
            source_code=context.source_code,
            file_path=context.file_path,
        )

        # 2. Semantic AST construction
        context.semantic_ast = self.semantic_builder.build(context.ast)

        # 3. Control Flow Graph construction
        context.cfg = self.cfg_builder.build(context.semantic_ast)

        # 4. Data Flow analysis
        context.data_flow = self.data_flow_builder.build(
            context.semantic_ast,
            context.cfg,
        )

        # 5. Interprocedural analysis
        context.interprocedural_graph = self.interprocedural_builder.build(
            context.semantic_ast,
            context.cfg,
            context.data_flow,
        )

        # 6. Execute Injection rule pack
        findings: List[Finding] = []

        for rule_cls in rule_package.rules:
            rule = rule_cls()
            findings.extend(rule.analyze(context))

        # 7. Return findings
        return findings
