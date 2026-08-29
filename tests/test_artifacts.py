import pytest
from engine.domain.artifacts.models import Artifact
from engine.domain.artifacts.registry import ArtifactRegistry
from engine.domain.artifacts.stores import InMemoryArtifactStore

def test_artifact_registry():
    registry = ArtifactRegistry()
    
    art1 = Artifact(id="1", stable_key="key1", kind="test_kind", file="test.py")
    art2 = Artifact(id="2", stable_key="key2", kind="test_kind", file="test.py")
    art3 = Artifact(id="3", stable_key="key3", kind="other_kind", file="other.py")
    
    # Test registration
    registry.register(art1)
    registry.register(art2)
    registry.register(art3)
    
    # Test lookups
    assert registry.get_by_id("1") == art1
    assert registry.get_by_stable_key("key2") == art2
    assert set(registry.get_by_file("test.py")) == {art1, art2}
    assert set(registry.get_by_kind("test_kind")) == {art1, art2}
    
    # Test duplicates
    with pytest.raises(ValueError):
        registry.register(Artifact(id="1", stable_key="new_key", kind="k", file="f"))
    with pytest.raises(ValueError):
        registry.register(Artifact(id="4", stable_key="key1", kind="k", file="f"))
        
    # Test update
    updated_art1 = Artifact(id="1", stable_key="key1_new", kind="test_kind", file="test2.py")
    registry.update(updated_art1)
    
    assert registry.get_by_stable_key("key1") is None
    assert registry.get_by_stable_key("key1_new") == updated_art1
    assert set(registry.get_by_file("test.py")) == {art2}
    assert set(registry.get_by_file("test2.py")) == {updated_art1}
    
    # Test removal
    registry.remove("1")
    assert registry.get_by_id("1") is None
    assert registry.get_by_stable_key("key1_new") is None
    assert registry.get_by_file("test2.py") == []
    
    # Test clear
    registry.clear()
    assert registry.get_by_id("2") is None


def test_in_memory_artifact_store():
    registry = ArtifactRegistry()
    store = InMemoryArtifactStore[Artifact](registry)
    
    art = Artifact(id="1", stable_key="k1", kind="k", file="f1")
    store.insert(art)
    
    assert store.get("1") == art
    assert store.find_by_stable_key("k1") == art
    assert store.find_by_file("f1") == [art]
    
    updated_art = Artifact(id="1", stable_key="k1_new", kind="k", file="f1")
    store.update(updated_art)
    
    assert store.find_by_stable_key("k1") is None
    assert store.find_by_stable_key("k1_new") == updated_art
    
    store.remove("1")
    assert store.get("1") is None
