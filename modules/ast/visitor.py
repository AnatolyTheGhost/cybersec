import ast as py_ast
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from engine.rule_engine import RuleEngine
    from engine.context import AnalysisContext


class BaseVisitor(py_ast.NodeVisitor):
    """
    Refactored AST Visitor.
    
    Responsibilities:
    - Traverses AST in depth-first order.
    - Updates AnalysisContext (scopes, taint propagation) during traversal.
    - Calls RuleEngine to evaluate rules on each node.
    - DOES NOT store findings (RuleEngine handles that).
    """

    def __init__(self, rule_engine: "RuleEngine", context: "AnalysisContext"):
        super().__init__()
        self.rule_engine = rule_engine
        self.context = context

    def visit(self, node: py_ast.AST):
        """
        Main entry point for each node.
        Updates context, evaluates rules, and then descends into children.
        """
        # 1. Update context (e.g. entering scopes, propagating taint)
        self._pre_visit_update(node)

        # 2. Delegate evaluation to the RuleEngine (findings stored internally in engine)
        self.rule_engine.analyze_node(node, self.context)

        # 3. Standard NodeVisitor dispatch (descends into children)
        result = super().visit(node)

        # 4. Context cleanup (e.g. exiting scopes)
        self._post_visit_update(node)

        return result

    def _pre_visit_update(self, node: py_ast.AST):
        """Update context before visiting node children."""
        if isinstance(node, (py_ast.FunctionDef, py_ast.AsyncFunctionDef, py_ast.ClassDef)):
            self.context.enter_scope(getattr(node, 'name', 'anonymous'))
        
        elif isinstance(node, py_ast.Assign):
            self._propagate_taint(node)

    def _post_visit_update(self, node: py_ast.AST):
        """Cleanup context after visiting node children."""
        if isinstance(node, (py_ast.FunctionDef, py_ast.AsyncFunctionDef, py_ast.ClassDef)):
            self.context.exit_scope()

    def _propagate_taint(self, node: py_ast.Assign):
        """
        Minimal taint propagation logic:
        If RHS contains a tainted name or is a source, mark LHS names as tainted.
        """
        # 1. Identify names in RHS
        rhs_names = {n.id for n in py_ast.walk(node.value) if isinstance(n, py_ast.Name)}
        
        # 2. Detection of source (simple pattern for demo)
        source_found = any(isinstance(n, py_ast.Attribute) and n.attr == 'environ' 
                           for n in py_ast.walk(node.value))
        
        # 3. Propagation
        if source_found or (rhs_names & self.context.tainted_names):
            for target in node.targets:
                if isinstance(target, py_ast.Name):
                    self.context.tainted_names.add(target.id)
                    self.context.mark_tainted(node.lineno)