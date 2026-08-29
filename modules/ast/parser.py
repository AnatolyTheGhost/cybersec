# Transform the code into an AST

import ast as py_ast
import uuid

from modules.ast.nodes import SourceRange


def _attach_provenance(node: py_ast.AST, filename: str) -> None:
    if not isinstance(node, py_ast.AST):
        return

    if not hasattr(node, "id"):
        setattr(node, "id", str(uuid.uuid4()))
    if not hasattr(node, "filename"):
        setattr(node, "filename", filename)
    if not hasattr(node, "source_range"):
        lineno = getattr(node, "lineno", None)
        end_lineno = getattr(node, "end_lineno", None)
        col_offset = getattr(node, "col_offset", None)
        end_col_offset = getattr(node, "end_col_offset", None)

        if lineno is None:
            lineno = 1
            end_lineno = 1
            col_offset = 0
            end_col_offset = 0
        else:
            if col_offset is None:
                col_offset = 0
            if end_col_offset is None:
                end_col_offset = col_offset
            if end_lineno is None:
                end_lineno = lineno

        setattr(
            node,
            "source_range",
            SourceRange(
                file=filename,
                start_line=lineno,
                start_column=col_offset,
                end_line=end_lineno,
                end_column=end_col_offset,
            ),
        )

    for child in py_ast.iter_child_nodes(node):
        _attach_provenance(child, filename)


class ASTParser:
    def parse(self, code: str, filename: str = "<unknown>"):
        try:
            tree = py_ast.parse(code, filename=filename)
            _attach_provenance(tree, filename)
            return tree
        except SyntaxError as e:
            raise ValueError(f"Invalid code: {e}")