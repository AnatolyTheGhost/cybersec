from dataclasses import dataclass
from typing import Iterable, Set
from .graph import DependencyGraph
from .state import ArtifactStateManager


@dataclass(frozen=True)
class InvalidationResult:
    """Result of an invalidation pass."""
    directly_changed: Set[str]
    affected: Set[str]


class InvalidationEngine:
    """
    Invalidates artifacts based on dependency graph relationships.
    Uses reverse dependencies (used_by) to propagate dirty states.
    """
    def __init__(self, graph: DependencyGraph, state_manager: ArtifactStateManager):
        self.graph = graph
        self.state_manager = state_manager

    def invalidate(self, changed_ids: Iterable[str]) -> InvalidationResult:
        """
        Invalidates the given changed artifact IDs and their transitive dependents.
        Updates the StateManager, marking all affected nodes as dirty.
        Returns a result differentiating directly changed vs transitively affected IDs.
        """
        directly_changed = set(changed_ids)
        
        # Ensure we only process nodes that exist in the graph
        valid_changed_ids = {uid for uid in directly_changed if self.graph.contains(uid)}
        
        # Discover all transitive dependents
        affected = set()
        for artifact_id in valid_changed_ids:
            # Add transitive dependents of this node
            deps = self.graph.traverse_dependents(artifact_id)
            affected.update(deps)

        # A node can't be both directly changed and transitively affected in the result semantics
        # (even if there are cycles or self-references). 
        # For clarity, 'affected' usually means "affected by something else changing".
        affected.difference_update(directly_changed)

        # Mark them all as dirty atomically (relative to state manager)
        all_invalidated = valid_changed_ids | affected
        if all_invalidated:
            self.state_manager.mark_dirty(all_invalidated)

        return InvalidationResult(
            directly_changed=valid_changed_ids,
            affected=affected
        )
