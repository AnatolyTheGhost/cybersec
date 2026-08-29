"""
LayerRunnerRegistry — maps task IDs to their LayerRunner implementations.

Decouples the planning Registry (metadata store) from the execution layer.
The WorkerPool resolves runners here before dispatching any task.
"""
from __future__ import annotations

from typing import Dict

from engine.runtime.layer_runner import LayerRunner


class RunnerNotFoundError(Exception):
    """Raised when a Task has no registered LayerRunner."""


class LayerRunnerRegistry:
    """
    Runtime registry that associates each Task ID with exactly one LayerRunner.

    This registry is intentionally separate from the planning Registry so
    that planning metadata remains decoupled from execution concerns.
    """

    def __init__(self) -> None:
        self._runners: Dict[str, LayerRunner] = {}

    def register(self, task_id: str, runner: LayerRunner) -> None:
        """
        Associate a LayerRunner with a Task ID.

        Overwrites any previously registered runner for the same ID to allow
        easy test setup and dynamic reconfiguration.
        """
        self._runners[task_id] = runner

    def get(self, task_id: str) -> LayerRunner:
        """
        Retrieve the LayerRunner for a Task ID.

        Raises:
            RunnerNotFoundError: if no runner is registered for *task_id*.
        """
        if task_id not in self._runners:
            raise RunnerNotFoundError(
                f"No LayerRunner registered for task '{task_id}'"
            )
        return self._runners[task_id]

    def has(self, task_id: str) -> bool:
        """Return True if a runner is registered for *task_id*."""
        return task_id in self._runners
