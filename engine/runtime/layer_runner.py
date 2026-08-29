"""
LayerRunner — the single execution contract for every analysis Task.

Every executable Task must be associated with exactly one LayerRunner.
WorkerPool never executes Task logic directly; it always delegates to a
LayerRunner resolved from the LayerRunnerRegistry.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from engine.core.planning.abstractions import Artifact
from engine.core.planning.analysis_context import AnalysisContext


class LayerRunner(ABC):
    """
    Abstract base class defining the execution contract for a Task.

    Implementations encapsulate all task-specific logic and return the
    Artifacts they produce. WorkerPool will store those Artifacts into the
    AnalysisContext on successful completion.
    """

    @abstractmethod
    async def execute(self, context: AnalysisContext) -> Sequence[Artifact]:
        """
        Execute the task and return the produced Artifacts.

        Args:
            context: The AnalysisContext for the current analysis session.
                     Runners may read existing artifacts from it but must
                     not write to it directly; WorkerPool owns that step.

        Returns:
            A sequence of Artifact instances produced by this task.
        """
        ...
