import ast
import uuid
import pytest
from typing import Dict, Any

from engine.incremental.mutations import MutationBatch, Mutation, MutationKind
from engine.incremental.provenance import ProvenanceIndex
from modules.semantic_ast.updater import SemanticASTUpdater, RAW_ASTIndex, SemanticParentIndex
from modules.semantic_ast.builder import SemanticBuilder
from modules.ast.parser import _attach_provenance


def parse_and_attach(code: str) -> ast.AST:
    tree = ast.parse(code)
    _attach_provenance(tree, "test.py")
    return tree

@pytest.fixture
def base_code():
    return """
def add(a, b):
    return a + b

class Helper:
    pass
"""

@pytest.fixture
def setup_ast(base_code):
    raw_ast = parse_and_attach(base_code)
    builder = SemanticBuilder()
    sem_ast = builder.build(raw_ast, "test.py")
    
    provenance = ProvenanceIndex()
    # Simple manual provenance registration for tests
    def register_tree(sem_node):
        if hasattr(sem_node, "source_ast_ids") and sem_node.source_ast_ids:
            provenance.register(sem_node.id, sem_node.source_ast_ids)
        for child in sem_node.children:
            register_tree(child)
            
    register_tree(sem_ast)
    return raw_ast, sem_ast, provenance


def test_raw_ast_index(setup_ast):
    raw_ast, _, _ = setup_ast
    index = RAW_ASTIndex(raw_ast)
    assert len(index.node_by_id) > 0
    assert len(index.parent_by_node) > 0

def test_semantic_parent_index(setup_ast):
    _, sem_ast, _ = setup_ast
    index = SemanticParentIndex(sem_ast)
    assert len(index.parent_by_node_id) > 0

def test_add_mutation(setup_ast):
    raw_ast, sem_ast, provenance = setup_ast
    
    # Mutate raw_ast to add a new function
    new_func_raw = parse_and_attach("def sub(a, b): return a - b").body[0]
    raw_ast.body.append(new_func_raw)
    
    mutation = Mutation(
        kind=MutationKind.ADD,
        entity_id=new_func_raw.id,
        base_version_id="v1",
        payload={"ast_node": new_func_raw}
    )
    batch = MutationBatch(base_version_id="v1", mutations=(mutation,))
    
    updater = SemanticASTUpdater()
    updated_root, results = updater.update(sem_ast, batch, provenance, raw_ast_root=raw_ast)
    
    assert results["added"] == 1
    # Check it was added to semantic AST
    func_names = [child.name for child in updated_root.children if hasattr(child, "name")]
    assert "sub" in func_names

def test_delete_mutation(setup_ast):
    raw_ast, sem_ast, provenance = setup_ast
    
    # Find the 'add' function
    add_func_raw = next(node for node in raw_ast.body if getattr(node, "name", "") == "add")
    
    mutation = Mutation(
        kind=MutationKind.DELETE,
        entity_id=add_func_raw.id,
        base_version_id="v1"
    )
    batch = MutationBatch(base_version_id="v1", mutations=(mutation,))
    
    updater = SemanticASTUpdater()
    updated_root, results = updater.update(sem_ast, batch, provenance, raw_ast_root=raw_ast)
    
    assert results["deleted"] == 1
    func_names = [child.name for child in updated_root.children if hasattr(child, "name")]
    assert "add" not in func_names

def test_update_mutation(setup_ast):
    raw_ast, sem_ast, provenance = setup_ast
    
    # Update 'Helper' class to 'SuperHelper'
    class_raw = next(node for node in raw_ast.body if getattr(node, "name", "") == "Helper")
    class_raw.name = "SuperHelper"
    
    mutation = Mutation(
        kind=MutationKind.UPDATE,
        entity_id=class_raw.id,
        base_version_id="v1",
        payload={"ast_node": class_raw}
    )
    batch = MutationBatch(base_version_id="v1", mutations=(mutation,))
    
    updater = SemanticASTUpdater()
    updated_root, results = updater.update(sem_ast, batch, provenance, raw_ast_root=raw_ast)
    
    assert results["updated"] == 1
    class_names = [child.name for child in updated_root.children if hasattr(child, "name")]
    assert "Helper" not in class_names
    assert "SuperHelper" in class_names
