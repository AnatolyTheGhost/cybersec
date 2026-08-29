from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone

from engine.core.planning.execution_dag import ExecutionDAG

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class TaskState:
    status: TaskStatus
    dependency_count: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    exception: Optional[Exception] = None

class ExecutionState:
    """
    Runtime execution state managing mutable execution data using Kahn's algorithm.
    """
    def __init__(self, dag: ExecutionDAG):
        self._states: Dict[str, TaskState] = {}
        for task in dag.topological_order():
            parents = dag.parents(task.id)
            dep_count = len(parents)
            status = TaskStatus.READY if dep_count == 0 else TaskStatus.PENDING
            self._states[task.id] = TaskState(status=status, dependency_count=dep_count)
            
    def get_state(self, task_id: str) -> TaskState:
        if task_id not in self._states:
            raise ValueError(f"Unknown task {task_id}")
        return self._states[task_id]
        
    def mark_task_started(self, task_id: str):
        state = self.get_state(task_id)
        if state.status != TaskStatus.READY:
            raise RuntimeError(f"Cannot start task {task_id} from status {state.status}")
        state.status = TaskStatus.RUNNING
        state.started_at = datetime.now(timezone.utc)
        
    def mark_task_finished(self, task_id: str, dag: ExecutionDAG, success: bool, error: Optional[Exception] = None) -> List[str]:
        """
        Marks a task as finished and decrements the dependency count of its children.
        Returns a list of newly READY task IDs.
        """
        state = self.get_state(task_id)
        state.status = TaskStatus.SUCCESS if success else TaskStatus.FAILED
        state.exception = error
        state.finished_at = datetime.now(timezone.utc)
        
        newly_ready = []
        if success:
            for child in dag.children(task_id):
                child_state = self.get_state(child.id)
                child_state.dependency_count -= 1
                if child_state.dependency_count == 0 and child_state.status == TaskStatus.PENDING:
                    child_state.status = TaskStatus.READY
                    newly_ready.append(child.id)
                    
        return newly_ready
