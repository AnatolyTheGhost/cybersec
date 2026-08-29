import threading
from collections import deque
from typing import Dict, Set

class DependencyGraph:
    """
    Centralized graph tracking dependencies between analysis artifacts.
    Operates on artifact UUIDs.
    Maintains forward (depends_on) and reverse (used_by) edges consistently.
    """
    def __init__(self):
        self._lock = threading.RLock()
        self._forward: Dict[str, Set[str]] = {}
        self._reverse: Dict[str, Set[str]] = {}

    def add_node(self, artifact_id: str) -> None:
        """Add an isolated node to the graph."""
        with self._lock:
            if artifact_id not in self._forward:
                self._forward[artifact_id] = set()
                self._reverse[artifact_id] = set()

    def remove_node(self, artifact_id: str) -> None:
        """Remove a node and all incoming/outgoing edges."""
        with self._lock:
            if artifact_id not in self._forward:
                return

            # Clean up outgoing edges
            for target_id in self._forward[artifact_id]:
                self._reverse[target_id].discard(artifact_id)
            del self._forward[artifact_id]

            # Clean up incoming edges
            for source_id in self._reverse[artifact_id]:
                self._forward[source_id].discard(artifact_id)
            del self._reverse[artifact_id]

    def add_dependency(self, source_id: str, target_id: str) -> None:
        """Add a dependency: source_id depends on target_id."""
        with self._lock:
            if source_id not in self._forward:
                raise ValueError(f"Source artifact {source_id} does not exist in graph.")
            if target_id not in self._forward:
                raise ValueError(f"Target artifact {target_id} does not exist in graph.")
            if source_id == target_id:
                raise ValueError("Self-dependencies are not allowed.")
            
            if target_id in self._forward[source_id]:
                return # Edge already exists

            # Check for cycles: if we add source -> target, would it create a cycle?
            # It creates a cycle if source can be reached from target.
            if self._can_reach(target_id, source_id):
                raise ValueError(f"Adding dependency {source_id} -> {target_id} creates a cycle.")

            self._forward[source_id].add(target_id)
            self._reverse[target_id].add(source_id)

    def remove_dependency(self, source_id: str, target_id: str) -> None:
        """Remove a dependency edge."""
        with self._lock:
            if source_id in self._forward and target_id in self._forward[source_id]:
                self._forward[source_id].remove(target_id)
                self._reverse[target_id].remove(source_id)

    def replace_dependencies(self, source_id: str, target_ids: Set[str]) -> None:
        """Atomically replace all dependencies for a node."""
        with self._lock:
            if source_id not in self._forward:
                raise ValueError(f"Source artifact {source_id} does not exist in graph.")
            
            for target_id in target_ids:
                if target_id not in self._forward:
                    raise ValueError(f"Target artifact {target_id} does not exist in graph.")
                if source_id == target_id:
                    raise ValueError("Self-dependencies are not allowed.")

            # Temporarily remove old edges to check cycles accurately for the new set
            old_targets = self._forward[source_id].copy()
            for old_target in old_targets:
                self._reverse[old_target].remove(source_id)
            self._forward[source_id].clear()

            try:
                for target_id in target_ids:
                    if self._can_reach(target_id, source_id):
                        raise ValueError(f"Adding dependencies creates a cycle involving {source_id} and {target_id}.")
                    self._forward[source_id].add(target_id)
                    self._reverse[target_id].add(source_id)
            except Exception as e:
                # Rollback
                for t in self._forward[source_id]:
                    self._reverse[t].remove(source_id)
                self._forward[source_id] = old_targets
                for t in old_targets:
                    self._reverse[t].add(source_id)
                raise e

    def get_direct_dependencies(self, artifact_id: str) -> Set[str]:
        """Query direct dependencies (depends_on)."""
        with self._lock:
            if artifact_id not in self._forward:
                raise KeyError(f"Artifact {artifact_id} not found.")
            return set(self._forward[artifact_id])

    def get_direct_dependents(self, artifact_id: str) -> Set[str]:
        """Query direct dependents (used_by)."""
        with self._lock:
            if artifact_id not in self._reverse:
                raise KeyError(f"Artifact {artifact_id} not found.")
            return set(self._reverse[artifact_id])

    def contains(self, artifact_id: str) -> bool:
        """Check if node exists."""
        with self._lock:
            return artifact_id in self._forward

    def clear(self) -> None:
        """Clear the entire graph."""
        with self._lock:
            self._forward.clear()
            self._reverse.clear()

    def _can_reach(self, start_id: str, end_id: str) -> bool:
        """Internal helper for cycle detection: returns True if start_id can reach end_id."""
        visited = set()
        queue = deque([start_id])
        while queue:
            current = queue.popleft()
            if current == end_id:
                return True
            if current not in visited:
                visited.add(current)
                queue.extend(self._forward.get(current, set()) - visited)
        return False

    def traverse_dependencies(self, artifact_id: str) -> Set[str]:
        """BFS traversal to find all transitive dependencies."""
        with self._lock:
            if artifact_id not in self._forward:
                raise KeyError(f"Artifact {artifact_id} not found.")
            
            result = set()
            queue = deque(self._forward[artifact_id])
            while queue:
                current = queue.popleft()
                if current not in result:
                    result.add(current)
                    queue.extend(self._forward.get(current, set()) - result)
            return result

    def traverse_dependents(self, artifact_id: str) -> Set[str]:
        """BFS traversal to find all transitive dependents."""
        with self._lock:
            if artifact_id not in self._reverse:
                raise KeyError(f"Artifact {artifact_id} not found.")
            
            result = set()
            queue = deque(self._reverse[artifact_id])
            while queue:
                current = queue.popleft()
                if current not in result:
                    result.add(current)
                    queue.extend(self._reverse.get(current, set()) - result)
            return result
