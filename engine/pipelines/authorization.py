"""
Authorization & Access Control Analysis Pipeline.

Fixed execution order:
Repository -> AST -> Semantic AST -> Framework Pass -> Endpoint Discovery -> Call Graph -> CFG -> Data Flow -> Interprocedural Analysis -> Authorization Rule Pack -> Findings
"""

import logging
from typing import Any, List

from engine.pipelines.base import BasePipeline
from rules.authorization.package import PACKAGE as AUTHORIZATION_PACKAGE
from rules.base.finding import Finding
from rules.base.package import RulePackage

logger = logging.getLogger(__name__)


class AuthorizationPipeline(BasePipeline):
    """
    Deterministic pipeline for Authorization & Access Control analysis.

    Execution order:
    AST -> Semantic AST -> Framework Detection -> Endpoint Discovery ->
    Call Graph -> CFG -> Data Flow -> Interprocedural Analysis ->
    Authorization Rule Pack -> Findings
    """

    def execute(
        self,
        workspace_path: str,
        rule_package: RulePackage = AUTHORIZATION_PACKAGE,
        context: Any = None,
    ) -> List[Finding]:

        logger.info("Executing AuthorizationPipeline on workspace: %s", workspace_path)

        # 1. AST construction
        context.ast = self.ast_builder.build(
            source_code=context.source_code,
            file_path=context.file_path,
        )

        # 2. Semantic AST construction
        context.semantic_ast = self.semantic_builder.build(context.ast)

        # 3. Framework detection
        context.framework = self.framework_detector.detect(
            context.semantic_ast,
        )

        # 4. Endpoint discovery
        context.endpoints = self.endpoint_discovery.build(
            context.semantic_ast,
            context.framework,
        )

        # 5. Call Graph construction
        context.call_graph = self.call_graph_builder.build(
            context.semantic_ast,
        )

        # 6. Control Flow Graph construction
        context.cfg = self.cfg_builder.build(
            context.semantic_ast,
        )

        # 7. Data Flow analysis
        context.data_flow = self.data_flow_analyzer.analyze(
            context.semantic_ast,
            context.cfg,
        )

        # 8. Interprocedural analysis
        context.interprocedural_graph = self.interprocedural_analyzer.analyze(
            context.semantic_ast,
            context.call_graph,
            context.data_flow,
        )

        # 9. Execute Authorization rule pack
        findings: List[Finding] = []

        for rule_cls in rule_package.rules:
            rule = rule_cls()
            findings.extend(rule.analyze(context))

        # 10. Return findings
        return findings