import pytest
from engine.domain.artifacts.graph import DependencyGraph
from engine.domain.artifacts.state import ArtifactStateManager
from engine.domain.artifacts.invalidation import InvalidationEngine

def setup_invalidation():
    graph = DependencyGraph()
    state = ArtifactStateManager()
    engine = InvalidationEngine(graph, state)
    return graph, state, engine

def test_single_node_invalidation():
    graph, state, engine = setup_invalidation()
    graph.add_node("A")
    
    result = engine.invalidate(["A"])
    assert result.directly_changed == {"A"}
    assert result.affected == set()
    assert state.is_dirty("A")

def test_linear_chain():
    graph, state, engine = setup_invalidation()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_node("C")
    graph.add_dependency("A", "B")
    graph.add_dependency("B", "C")
    
    result = engine.invalidate(["C"])
    assert result.directly_changed == {"C"}
    assert result.affected == {"B", "A"}
    
    assert state.is_dirty("C")
    assert state.is_dirty("B")
    assert state.is_dirty("A")

def test_branching_dependencies():
    graph, state, engine = setup_invalidation()
    for n in ["A", "B", "C", "D"]:
        graph.add_node(n)
        
    graph.add_dependency("B", "A")
    graph.add_dependency("C", "A")
    graph.add_dependency("D", "B")
    
    # D -> B -> A
    #      C -> A
    
    result = engine.invalidate(["A"])
    assert result.directly_changed == {"A"}
    assert result.affected == {"B", "C", "D"}

def test_multiple_changed_roots():
    graph, state, engine = setup_invalidation()
    for n in ["A", "B", "C", "D", "E"]:
        graph.add_node(n)
        
    graph.add_dependency("C", "A")
    graph.add_dependency("D", "B")
    graph.add_dependency("E", "C")
    
    # E -> C -> A
    # D -> B
    
    result = engine.invalidate(["A", "B"])
    assert result.directly_changed == {"A", "B"}
    assert result.affected == {"C", "D", "E"}
    
    for n in ["A", "B", "C", "D", "E"]:
        assert state.is_dirty(n)

def test_unrelated_nodes():
    graph, state, engine = setup_invalidation()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_dependency("B", "A")
    
    graph.add_node("C")
    graph.add_node("D")
    graph.add_dependency("D", "C")
    
    result = engine.invalidate(["A"])
    assert result.directly_changed == {"A"}
    assert result.affected == {"B"}
    
    assert state.is_dirty("A")
    assert state.is_dirty("B")
    assert not state.is_dirty("C")
    assert not state.is_dirty("D")

def test_version_bump_and_state():
    state = ArtifactStateManager()
    
    assert state.get_version("A") == 1
    state.mark_dirty(["A"])
    assert state.is_dirty("A")
    
    new_version = state.bump_version("A")
    assert new_version == 2
    assert state.get_version("A") == 2
    
    state.mark_clean(["A"])
    assert not state.is_dirty("A")

def test_removal_handling():
    state = ArtifactStateManager()
    state.mark_dirty(["A"])
    state.bump_version("A")
    
    state.remove("A")
    assert not state.is_dirty("A")
    assert state.get_version("A") == 1
