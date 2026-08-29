from modules.ast.visitor import BaseVisitor


class ASTTraverser:
    def __init__(self, visitor: BaseVisitor):
        self.visitor = visitor

    def traverse(self, tree):
        """
        Запускает обход AST дерева.
        """
        self.visitor.visit(tree)