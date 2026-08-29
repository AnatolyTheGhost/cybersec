"""
WorkerPool — asynchronous executor for Tasks in an ExecutionDAG.

The WorkerPool is the only component that bridges the planning layer
(ExecutionDAG, ExecutionState) with the execution layer (LayerRunner).

Responsibilities
----------------
* Drive the Kahn's-algorithm loop held by ExecutionState.
* Dispatch READY tasks to their LayerRunners concurrently.
* Store produced Artifacts into the AnalysisContext.
* Propagate failures cleanly without cancelling in-flight work.

Non-responsibilities
--------------------
* Dependency resolution (owned by ExecutionState / Planner).
* DAG construction or modification.
* Retry logic.
* Distributed execution.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from engine.core.planning.execution_dag import ExecutionDAG
from engine.core.planning.analysis_context import AnalysisContext
from engine.runtime.execution_state import ExecutionState, TaskStatus
from engine.runtime.layer_runner_registry import LayerRunnerRegistry

log = logging.getLogger(__name__)

_DEFAULT_MAX_WORKERS = 4


class WorkerPoolError(Exception):
    """Raised when WorkerPool execution fails due to a task error."""

    def __init__(self, task_id: str, cause: Exception) -> None:
        super().__init__(f"Task '{task_id}' failed: {cause}")
        self.task_id = task_id
        self.cause = cause


class WorkerPool:
    """
    Asynchronous WorkerPool that executes Tasks from an ExecutionDAG.

    Uses asyncio with a bounded Semaphore to cap concurrency at
    *max_workers* simultaneous tasks.
    """

    def __init__(
        self,
        registry: LayerRunnerRegistry,
        max_workers: int = _DEFAULT_MAX_WORKERS,
    ) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        self._registry = registry
        self._max_workers = max_workers

    async def run(
        self,
        dag: ExecutionDAG,
        state: ExecutionState,
        context: AnalysisContext,
    ) -> None:
        """
        Execute all Tasks in *dag*, respecting dependency ordering.

        Updates *state* using Kahn's algorithm as tasks complete and stores
        produced Artifacts into *context*. Raises WorkerPoolError on the
        first task failure (after all in-flight tasks have settled).
        """
        semaphore = asyncio.Semaphore(self._max_workers)
        queue: asyncio.Queue[str] = asyncio.Queue()

        # Seed the queue with all initially READY tasks.
        for task in dag.topological_order():
            if state.get_state(task.id).status == TaskStatus.READY:
                await queue.put(task.id)

        # Track in-flight asyncio Tasks by task_id.
        in_flight: dict[str, asyncio.Task] = {}
        first_error: Optional[WorkerPoolError] = None
        stop_scheduling = False

        async def _dispatch(task_id: str) -> None:
            """Run one Task inside the semaphore, update state + context."""
            nonlocal first_error, stop_scheduling

            async with semaphore:
                state.mark_task_started(task_id)
                log.debug("Started task '%s'", task_id)

                try:
                    runner = self._registry.get(task_id)
                    artifacts = await runner.execute(context)
                except Exception as exc:  # noqa: BLE001
                    log.error("Task '%s' failed: %s", task_id, exc)
                    state.mark_task_finished(task_id, dag, success=False, error=exc)
                    if first_error is None:
                        first_error = WorkerPoolError(task_id, exc)
                    stop_scheduling = True
                    return

                # Success path: persist artifacts and unlock dependents.
                for artifact in artifacts:
                    context.add_artifact(artifact)

                newly_ready: List[str] = state.mark_task_finished(
                    task_id, dag, success=True
                )
                log.debug(
                    "Task '%s' succeeded; newly ready: %s", task_id, newly_ready
                )

                if not stop_scheduling:
                    for child_id in newly_ready:
                        await queue.put(child_id)

        # Main scheduling loop: drain the queue while in-flight work exists.
        while True:
            # Collect any IDs waiting in the queue right now.
            pending_ids: List[str] = []
            try:
                while True:
                    pending_ids.append(queue.get_nowait())
            except asyncio.QueueEmpty:
                pass

            for task_id in pending_ids:
                if not stop_scheduling:
                    asyncio_task = asyncio.create_task(
                        _dispatch(task_id), name=f"worker-{task_id}"
                    )
                    in_flight[task_id] = asyncio_task
                queue.task_done()

            # Remove completed asyncio tasks from in_flight.
            done_ids = [tid for tid, t in in_flight.items() if t.done()]
            for tid in done_ids:
                del in_flight[tid]

            if not in_flight:
                # Nothing running and nothing queued — we are done.
                break

            # Yield control so dispatched coroutines can make progress.
            await asyncio.sleep(0)

        # Final sweep: wait for any remaining in-flight tasks.
        if in_flight:
            await asyncio.gather(*in_flight.values(), return_exceptions=True)

        if first_error is not None:
            raise first_error
