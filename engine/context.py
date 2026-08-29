from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AnalysisContext:
    """
    Shared analysis context passed through the entire pipeline.
    Every stage stores its artifacts here for downstream stages.
    """

    # Input
    source_code: str
    workspace_path: str

    # Parsing
    ast: Any | None = None
    semantic_ast: Any | None = None

    # Framework analysis
    framework: Any | None = None
    framework_info: Any | None = None
    endpoints: Any | None = None

    # Graphs
    cfg: Any | None = None
    call_graph: Any | None = None

    # Analysis artifacts
    data_flow: Any | None = None
    interprocedural_graph: Any | None = None

    # Results
    findings: list[Any] = field(default_factory=list)