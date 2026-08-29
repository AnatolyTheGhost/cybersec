import ast
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Set

logger = logging.getLogger(__name__)

from engine.incremental.mutations import MutationBatch, MutationKind, Mutation
from engine.incremental.provenance import ProvenanceIndex
from modules.semantic_ast.nodes import SemanticNode, ModuleNode
from modules.semantic_ast.builder import SemanticBuilder


class RAW_ASTIndex:
    """
    Helper to index RAW AST nodes by ID and track their structural parents.
    Addresses the gap that Python's ast module does not natively support
    parent pointers or position-based lookup by entity ID.
    """
    def __init__(self, root: ast.AST):
        self.node_by_id: Dict[str, ast.AST] = {}
        self.parent_by_node: Dict[ast.AST, ast.AST] = {}
        self.children_lists: Dict[ast.AST, Dict[str, List[ast.AST]]] = {}
        self._build(root)

    def _build(self, node: ast.AST, parent: Optional[ast.AST] = None):
        if hasattr(node, "id"):
            self.node_by_id[str(node.id)] = node
        if parent is not None:
            self.parent_by_node[node] = parent
            
        for fieldname, value in ast.iter_fields(node):
            if isinstance(value, list):
                if node not in self.children_lists:
                    self.children_lists[node] = {}
                self.children_lists[node][fieldname] = [v for v in value if isinstance(v, ast.AST)]
                for item in value:
                    if isinstance(item, ast.AST):
                        self._build(item, node)
            elif isinstance(value, ast.AST):
                self._build(value, node)


class SemanticParentIndex:
    """
    Helper to index SemanticNode parents to allow structural updates.
    """
    def __init__(self, root: SemanticNode):
        self.parent_by_node_id: Dict[str, SemanticNode] = {}
        self.node_by_id: Dict[str, SemanticNode] = {}
        self._build(root)

    def _build(self, node: SemanticNode, parent: Optional[SemanticNode] = None):
        self.node_by_id[node.id] = node
        if parent is not None:
            self.parent_by_node_id[node.id] = parent
        for child in node.children:
            self._build(child, node)

    def replace_node(self, old_node: SemanticNode, new_node: SemanticNode):
        parent = self.parent_by_node_id.get(old_node.id)
        if not parent:
            return
        
        # Replace in children
        try:
            idx = parent.children.index(old_node)
            parent.children[idx] = new_node
        except ValueError:
            pass

        # Update specific fields if any (like targets, body, etc)
        for field, value in vars(parent).items():
            if value is old_node:
                setattr(parent, field, new_node)
            elif isinstance(value, list) and old_node in value:
                idx = value.index(old_node)
                value[idx] = new_node

        self.parent_by_node_id[new_node.id] = parent
        if old_node.id in self.parent_by_node_id:
            del self.parent_by_node_id[old_node.id]

    def remove_node(self, old_node: SemanticNode):
        parent = self.parent_by_node_id.get(old_node.id)
        if not parent:
            return
        
        if old_node in parent.children:
            parent.children.remove(old_node)
            
        for field, value in vars(parent).items():
            if value is old_node:
                setattr(parent, field, None)
            elif isinstance(value, list) and old_node in value:
                value.remove(old_node)
        
        if old_node.id in self.parent_by_node_id:
            del self.parent_by_node_id[old_node.id]


class SemanticASTUpdater:
    def __init__(self):
        self.builder = SemanticBuilder()

    def update(
        self, 
        root_node: SemanticNode, 
        batch: MutationBatch, 
        provenance: ProvenanceIndex,
        raw_ast_root: Optional[ast.AST] = None
    ) -> Tuple[SemanticNode, Dict[str, Any]]:
        """
        Applies mutations incrementally and updates structural references.
        Returns the updated root and a result summary.
        """
        if raw_ast_root is None:
            raise ValueError("raw_ast_root is required to determine structural positions.")
            
        raw_index = RAW_ASTIndex(raw_ast_root)
        sem_index = SemanticParentIndex(root_node)
        
        results = {"added": 0, "updated": 0, "deleted": 0}

        for mutation in batch.mutations:
            start_time = time.perf_counter()
            status = "FAILED"
            try:
                if mutation.kind == MutationKind.ADD:
                    if self._handle_add(mutation, root_node, raw_index, sem_index, provenance):
                        results["added"] += 1
                        status = "SUCCESS"
                elif mutation.kind == MutationKind.UPDATE:
                    if self._handle_update(mutation, raw_index, sem_index, provenance):
                        results["updated"] += 1
                        status = "SUCCESS"
                elif mutation.kind == MutationKind.DELETE:
                    if self._handle_delete(mutation, raw_index, sem_index, provenance):
                        results["deleted"] += 1
                        status = "SUCCESS"
            except Exception as e:
                status = f"ERROR: {str(e)}"
                logger.error("Exception processing mutation %s: %s", mutation.entity_id, e, exc_info=True)
            finally:
                elapsed = time.perf_counter() - start_time
                logger.info(
                    "Operation: %s | Node ID: %s | Status: %s | Time: %.4fs | Full Response (current batch results): %s",
                    mutation.kind.value,
                    mutation.entity_id,
                    status,
                    elapsed,
                    results
                )

        return root_node, results

    def _handle_add(
        self, 
        mutation: Mutation, 
        root_node: SemanticNode,
        raw_index: RAW_ASTIndex, 
        sem_index: SemanticParentIndex, 
        provenance: ProvenanceIndex
    ) -> bool:
        raw_node = raw_index.node_by_id.get(mutation.entity_id)
        if not raw_node:
            return False

        new_sem_node = self.builder.visit(raw_node)
        if not new_sem_node:
            return False
            
        # Register new provenance (visit already attaches source_ast_ids internally, but let's ensure)
        origin_ids = getattr(new_sem_node, "source_ast_ids", set())
        if origin_ids:
            provenance.register(new_sem_node.id, origin_ids)

        raw_parent = raw_index.parent_by_node.get(raw_node)
        if raw_parent:
            parent_origin_id = str(getattr(raw_parent, "id", ""))
            if parent_origin_id:
                sem_parent_ids = provenance.lookup_derived(parent_origin_id)
                if sem_parent_ids:
                    sem_parent_id = next(iter(sem_parent_ids)) # Just take one if multiple
                    
                    # Need to find actual semantic node
                    sem_parent = self._find_node_by_id(root_node, sem_parent_id)
                    if sem_parent:
                        # Append to children for now. Precise placement depends on field
                        sem_parent.children.append(new_sem_node)
                        # Find which field it was in raw AST
                        lists = raw_index.children_lists.get(raw_parent, {})
                        for field, items in lists.items():
                            if raw_node in items:
                                # We found the list field, but in semantic AST, fields like 'body' or 'children' are lists
                                if hasattr(sem_parent, field) and isinstance(getattr(sem_parent, field), list):
                                    getattr(sem_parent, field).append(new_sem_node)
                        sem_index._build(new_sem_node, sem_parent)
        return True

    def _handle_update(
        self, 
        mutation: Mutation, 
        raw_index: RAW_ASTIndex,
        sem_index: SemanticParentIndex, 
        provenance: ProvenanceIndex
    ) -> bool:
        derived_ids = provenance.lookup_derived(mutation.entity_id)
        if not derived_ids:
            return False
            
        raw_node = raw_index.node_by_id.get(mutation.entity_id)
        if not raw_node:
            if mutation.payload and "ast_node" in mutation.payload:
                raw_node = mutation.payload["ast_node"]
            
        if not raw_node:
            return False

        new_sem_node = self.builder.visit(raw_node)
        if not new_sem_node:
            return False

        for sem_id in derived_ids:
            old_node = sem_index.node_by_id.get(sem_id)
            
            if old_node:
                sem_index.replace_node(old_node, new_sem_node)
                provenance.remove(sem_id)
        
        origin_ids = getattr(new_sem_node, "source_ast_ids", set())
        if origin_ids:
            provenance.register(new_sem_node.id, origin_ids)
        return True

    def _handle_delete(
        self, 
        mutation: Mutation, 
        raw_index: RAW_ASTIndex,
        sem_index: SemanticParentIndex, 
        provenance: ProvenanceIndex
    ) -> bool:
        derived_ids = provenance.lookup_derived(mutation.entity_id)
        deleted_any = False
        for sem_id in derived_ids:
            old_node = sem_index.node_by_id.get(sem_id)
            
            if old_node:
                sem_index.remove_node(old_node)
                provenance.remove(sem_id)
                deleted_any = True
        return deleted_any

    def _find_node_by_id(self, root: SemanticNode, target_id: str) -> Optional[SemanticNode]:
        if root.id == target_id:
            return root
        for child in root.children:
            res = self._find_node_by_id(child, target_id)
            if res:
                return res
        return None
