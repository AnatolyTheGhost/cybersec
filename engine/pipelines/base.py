from __future__ import annotations

from abc import ABC, abstractmethod

from modules.ast.builder import ASTBuilder
from modules.semantic_ast.builder import SemanticBuilder

from rules.base.finding import Finding
from rules.base.package import RulePackage
from engine.context import AnalysisContext


class _NoOpComponent:
    """Minimal compatibility shim for optional analysis stages in the MVP."""

    def detect(self, *args, **kwargs):
        return None

    def build(self, *args, **kwargs):
        return None

    def analyze(self, *args, **kwargs):
        return None


class BasePipeline(ABC):
    """
    Base class for deterministic analysis pipelines.

    Owns the common builders shared by every pipeline.
    """

    def __init__(self) -> None:
        self.ast_builder = ASTBuilder()
        self.semantic_builder = SemanticBuilder()
        self.framework_detector = _NoOpComponent()
        self.endpoint_discovery = _NoOpComponent()
        self.call_graph_builder = _NoOpComponent()
        self.cfg_builder = _NoOpComponent()
        self.data_flow_builder = _NoOpComponent()
        self.data_flow_analyzer = _NoOpComponent()
        self.interprocedural_builder = _NoOpComponent()
        self.interprocedural_analyzer = _NoOpComponent()

    @abstractmethod
    def execute(
        self,
        workspace_path: str,
        rule_package: RulePackage,
        context: AnalysisContext,
    ) -> list[Finding]:
        ...
