from __future__ import annotations

import ast
import asyncio
import logging
from typing import TYPE_CHECKING, Sequence

from engine.core.planning.abstractions import Artifact, Task
from engine.runtime.layer_runner import LayerRunner
from modules.ast.visitor import BaseVisitor
from modules.ast.builder import ASTBuilder

if TYPE_CHECKING:
    from engine.core.planning.analysis_context import AnalysisContext
    from engine.rule_engine import RuleEngine
    from config_engine import AnalysisConfig

log = logging.getLogger(__name__)

AstAnalysisTask = Task(
    id="ast.analysis",
    consumes=["source_code"],
    produces=["ast"],
    required_capabilities=["ast_parse"],
    required_features=["python_ast"],
    supported_strategies=["default"],
)


class AstLayerRunner(LayerRunner):
    """Parse source text into an AST and expose it as an immutable artifact."""

    async def execute(self, context: "AnalysisContext") -> Sequence[Artifact]:
        source_code = self._read_value(context, "source_code")
        file_path = self._read_value(context, "file_path") or "unknown.py"

        if not source_code:
            return []

        ast_builder = ASTBuilder()
        ast_tree = ast_builder.build(source_code, file_path=file_path)
        self._store_value(context, "ast_tree", ast_tree)
        self._store_value(context, "source_code", source_code)
        self._store_value(context, "file_path", file_path)

        artifact = Artifact(
            id=f"artifact-{AstAnalysisTask.id}",
            artifact_type=AstAnalysisTask.produces[0],
            version="1",
        )
        return [artifact]

    def run(
        self,
        context: "AnalysisContext",
        config: "AnalysisConfig" | None = None,
        rule_engine: "RuleEngine" | None = None,
    ) -> Sequence[Artifact]:
        artifacts = asyncio.run(self.execute(context))
        if rule_engine is not None:
            ast_tree = self._read_value(context, "ast_tree")
            if ast_tree is not None:
                visitor = BaseVisitor(rule_engine, context)
                visitor.visit(ast_tree)
        return artifacts

    @staticmethod
    def _read_value(context: "AnalysisContext", attr_name: str):
        if hasattr(context, attr_name):
            return getattr(context, attr_name)
        metadata = getattr(context, "metadata", None)
        if isinstance(metadata, dict):
            return metadata.get(attr_name)
        return None

    @staticmethod
    def _store_value(context: "AnalysisContext", attr_name: str, value) -> None:
        if hasattr(context, attr_name):
            setattr(context, attr_name, value)
        metadata = getattr(context, "metadata", None)
        if isinstance(metadata, dict):
            metadata[attr_name] = value

