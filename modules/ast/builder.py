import ast
from typing import Union

class ASTBuilder:
    """
    ASTBuilder parses Python source code into a standard Python AST.
    """
    def build(self, source_code: str, workspace_path: str = "<unknown>") -> ast.AST:
        try:
            return ast.parse(source_code, filename=workspace_path)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code in {workspace_path}: {e}") from e
