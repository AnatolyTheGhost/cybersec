import pytest
from engine.domain.artifacts.graph import DependencyGraph

def test_add_remove_node():
    graph = DependencyGraph()
    graph.add_node("A")
    assert graph.contains("A")
    graph.remove_node("A")
    assert not graph.contains("A")

def test_dependencies():
    graph = DependencyGraph()
    graph.add_node("A")
    graph.add_node("B")
    
    graph.add_dependency("A", "B")
    assert graph.get_direct_dependencies("A") == {"B"}
    assert graph.get_direct_dependents("B") == {"A"}
    
    graph.remove_dependency("A", "B")
    assert graph.get_direct_dependencies("A") == set()
    assert graph.get_direct_dependents("B") == set()

def test_node_removal_clears_edges():
    graph = DependencyGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_node("C")
    
    graph.add_dependency("A", "B")
    graph.add_dependency("B", "C")
    
    graph.remove_node("B")
    assert graph.get_direct_dependencies("A") == set()
    assert graph.get_direct_dependents("C") == set()

def test_cycle_detection():
    graph = DependencyGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_node("C")
    
    graph.add_dependency("A", "B")
    graph.add_dependency("B", "C")
    
    with pytest.raises(ValueError, match="cycle"):
        graph.add_dependency("C", "A")

def test_replace_dependencies():
    graph = DependencyGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_node("C")
    
    graph.add_dependency("A", "B")
    graph.replace_dependencies("A", {"C"})
    
    assert graph.get_direct_dependencies("A") == {"C"}
    assert graph.get_direct_dependents("B") == set()
    assert graph.get_direct_dependents("C") == {"A"}

def test_traversal():
    graph = DependencyGraph()
    graph.add_node("A")
    graph.add_node("B")
    graph.add_node("C")
    graph.add_node("D")
    
    graph.add_dependency("A", "B")
    graph.add_dependency("B", "C")
    graph.add_dependency("A", "D")
    
    assert graph.traverse_dependencies("A") == {"B", "C", "D"}
    assert graph.traverse_dependents("C") == {"B", "A"}
