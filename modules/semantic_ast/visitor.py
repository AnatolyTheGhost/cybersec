from typing import Any
from modules.semantic_ast.nodes import (
    SemanticNode,
    ModuleNode,
    ImportNode,
    ClassNode,
    FunctionNode,
    ParameterNode,
    VariableNode,
    AssignmentNode,
    CallNode,
    ReturnNode,
    IfNode,
    ForNode,
    WhileNode,
    LiteralNode,
    IdentifierNode,
)

class SemanticASTVisitor:
    """
    A visitor pattern implementation for language-agnostic Semantic AST.
    """
    def visit(self, node: SemanticNode) -> Any:
        if node is None:
            return None
        method_name = f"visit_{node.kind}"
        visitor_method = getattr(self, method_name, self.generic_visit)
        return visitor_method(node)

    def generic_visit(self, node: SemanticNode) -> Any:
        for child in node.children:
            self.visit(child)

    def visit_Module(self, node: ModuleNode) -> Any:
        return self.generic_visit(node)

    def visit_Import(self, node: ImportNode) -> Any:
        return self.generic_visit(node)

    def visit_Class(self, node: ClassNode) -> Any:
        return self.generic_visit(node)

    def visit_Function(self, node: FunctionNode) -> Any:
        return self.generic_visit(node)

    def visit_Parameter(self, node: ParameterNode) -> Any:
        return self.generic_visit(node)

    def visit_Variable(self, node: VariableNode) -> Any:
        return self.generic_visit(node)

    def visit_Assignment(self, node: AssignmentNode) -> Any:
        return self.generic_visit(node)

    def visit_Call(self, node: CallNode) -> Any:
        return self.generic_visit(node)

    def visit_Return(self, node: ReturnNode) -> Any:
        return self.generic_visit(node)

    def visit_If(self, node: IfNode) -> Any:
        return self.generic_visit(node)

    def visit_For(self, node: ForNode) -> Any:
        return self.generic_visit(node)

    def visit_While(self, node: WhileNode) -> Any:
        return self.generic_visit(node)

    def visit_Literal(self, node: LiteralNode) -> Any:
        return self.generic_visit(node)

    def visit_Identifier(self, node: IdentifierNode) -> Any:
        return self.generic_visit(node)
