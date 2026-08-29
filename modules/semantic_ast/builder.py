import ast
from typing import Any, List, Optional, Union

from modules.ast.nodes import SourceRange
from modules.semantic_ast.nodes import (
    AssignmentNode,
    CallNode,
    ClassNode,
    ForNode,
    FunctionNode,
    IdentifierNode,
    IfNode,
    ImportNode,
    LiteralNode,
    ModuleNode,
    ParameterNode,
    ReturnNode,
    SemanticNode,
    VariableNode,
    WhileNode,
)


def _get_source_range(node: ast.AST, *, filename: Optional[str] = None) -> Optional[SourceRange]:
    if hasattr(node, "source_range"):
        source_range = node.source_range
        file_name = filename or getattr(node, "filename", None) or "<unknown>"
        if getattr(source_range, "file", "<unknown>") == "<unknown>" or getattr(source_range, "file", None) != file_name:
            return SourceRange(
                file=file_name,
                start_line=source_range.start_line,
                start_column=source_range.start_column,
                end_line=source_range.end_line,
                end_column=source_range.end_column,
            )
        return source_range
    if hasattr(node, "lineno") and hasattr(node, "col_offset"):
        end_line = getattr(node, "end_lineno", node.lineno)
        end_col = getattr(node, "end_col_offset", node.col_offset)
        if end_line is None:
            end_line = node.lineno
        if end_col is None:
            end_col = node.col_offset
        return SourceRange(
            file=getattr(node, "filename", "<unknown>"),
            start_line=node.lineno,
            start_column=node.col_offset,
            end_line=end_line,
            end_column=end_col,
        )
    return None


class SemanticBuilder:
    capability = "semantic_builder"
    consumes = ["RAW_AST"]
    produces = ["SEMANTIC_AST"]

    def __init__(self):
        self.in_class = False
        self.filename = "<unknown>"

    def build(self, ast_or_source: Union[ast.AST, str], filename: str = "<unknown>") -> ModuleNode:
        self.filename = filename
        if isinstance(ast_or_source, str):
            ast_node = ast.parse(ast_or_source, filename=filename)
        else:
            ast_node = ast_or_source
            if getattr(ast_node, "filename", None) is None:
                setattr(ast_node, "filename", filename)

        result = self.visit(ast_node)
        if isinstance(result, ModuleNode):
            return self._attach_provenance(ast_node, result, filename=filename)
        module = ModuleNode(source_range=_get_source_range(ast_node, filename=filename), children=[result] if result else [])
        return self._attach_provenance(ast_node, module, result, filename=filename)

    def _attach_provenance(self, ast_node: ast.AST, sem_node: SemanticNode, *children: Optional[SemanticNode], filename: Optional[str] = None) -> SemanticNode:
        source_ast_ids = set()
        filename = filename or self.filename
        ast_id = getattr(ast_node, "id", None)
        if ast_id is not None:
            source_ast_ids.add(ast_id)
        for child in children:
            if child is None:
                continue
            source_ast_ids.update(getattr(child, "source_ast_ids", set()))
        sem_node.source_range = _get_source_range(ast_node, filename=filename)
        sem_node.source_ast_ids = source_ast_ids
        return sem_node

    def visit(self, node: ast.AST) -> Optional[SemanticNode]:
        if node is None:
            return None

        method_name = f"visit_{node.__class__.__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast.AST) -> Optional[SemanticNode]:
        children = []
        for child_ast in ast.iter_child_nodes(node):
            child_sem = self.visit(child_ast)
            if child_sem:
                children.append(child_sem)

        if children:
            sem_node = SemanticNode(children=children)
            return self._attach_provenance(node, sem_node, *children)
        return None

    def _visit_list(self, nodes: List[ast.AST]) -> List[SemanticNode]:
        results = []
        for n in nodes:
            res = self.visit(n)
            if res:
                results.append(res)
        return results

    def visit_Module(self, node: ast.Module) -> ModuleNode:
        docstring = ast.get_docstring(node)
        children = self._visit_list(node.body)

        sem_node = ModuleNode(children=children, docstring=docstring)
        return self._attach_provenance(node, sem_node, *children)

    def visit_Import(self, node: ast.Import) -> ImportNode:
        names = [alias.name for alias in node.names]
        sem_node = ImportNode(names=names)
        return self._attach_provenance(node, sem_node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ImportNode:
        names = [alias.name for alias in node.names]
        module_name = node.module or ""
        sem_node = ImportNode(module_name=module_name, names=names)
        return self._attach_provenance(node, sem_node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ClassNode:
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                parts = []
                curr = base
                while isinstance(curr, ast.Attribute):
                    parts.append(curr.attr)
                    curr = curr.value
                if isinstance(curr, ast.Name):
                    parts.append(curr.id)
                bases.append(".".join(reversed(parts)))

        was_in_class = self.in_class
        self.in_class = True
        body = self._visit_list(node.body)
        self.in_class = was_in_class

        sem_node = ClassNode(children=body, name=node.name, bases=bases)
        return self._attach_provenance(node, sem_node, *body)

    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> FunctionNode:
        parameters = []
        all_args = []
        if hasattr(node.args, "posonlyargs"):
            all_args.extend(node.args.posonlyargs)
        all_args.extend(node.args.args)
        all_args.extend(node.args.kwonlyargs)
        if node.args.vararg:
            all_args.append(node.args.vararg)
        if node.args.kwarg:
            all_args.append(node.args.kwarg)

        for arg in all_args:
            annotation_str = None
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    annotation_str = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    annotation_str = str(arg.annotation.value)

            param_node = ParameterNode(name=arg.arg, type_annotation=annotation_str)
            parameters.append(param_node)

        body = self._visit_list(node.body)

        sem_node = FunctionNode(children=parameters + body, name=node.name, parameters=parameters, is_method=self.in_class)
        return self._attach_provenance(node, sem_node, *parameters, *body)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> FunctionNode:
        return self.visit_FunctionDef(node)

    def visit_Assign(self, node: ast.Assign) -> AssignmentNode:
        targets = self._visit_list(node.targets)
        value = self.visit(node.value)

        children = targets[:]
        if value:
            children.append(value)

        sem_node = AssignmentNode(children=children, targets=targets, value=value)
        return self._attach_provenance(node, sem_node, *children)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> AssignmentNode:
        target = self.visit(node.target)
        value = self.visit(node.value) if node.value else None

        annotation_str = None
        if isinstance(node.annotation, ast.Name):
            annotation_str = node.annotation.id
        if isinstance(target, VariableNode):
            target.type_annotation = annotation_str
        elif isinstance(target, IdentifierNode):
            target = VariableNode(
                id=target.id,
                source_range=target.source_range,
                source_ast_ids=target.source_ast_ids,
                children=target.children,
                language=target.language,
                attributes=target.attributes,
                name=target.name,
                type_annotation=annotation_str,
            )

        children = [target]
        if value:
            children.append(value)

        sem_node = AssignmentNode(children=children, targets=[target], value=value)
        return self._attach_provenance(node, sem_node, *children)

    def visit_Name(self, node: ast.Name) -> Union[VariableNode, IdentifierNode]:
        if isinstance(node.ctx, ast.Store):
            sem_node = VariableNode(name=node.id)
            return self._attach_provenance(node, sem_node)
        sem_node = IdentifierNode(name=node.id)
        return self._attach_provenance(node, sem_node)

    def visit_Constant(self, node: ast.Constant) -> LiteralNode:
        sem_node = LiteralNode(value=node.value)
        return self._attach_provenance(node, sem_node)

    def visit_Num(self, node: ast.Num) -> LiteralNode:
        sem_node = LiteralNode(value=node.n)
        return self._attach_provenance(node, sem_node)

    def visit_Str(self, node: ast.Str) -> LiteralNode:
        sem_node = LiteralNode(value=node.s)
        return self._attach_provenance(node, sem_node)

    def visit_Bytes(self, node: ast.Bytes) -> LiteralNode:
        sem_node = LiteralNode(value=node.s)
        return self._attach_provenance(node, sem_node)

    def visit_NameConstant(self, node: ast.NameConstant) -> LiteralNode:
        sem_node = LiteralNode(value=node.value)
        return self._attach_provenance(node, sem_node)

    def visit_Call(self, node: ast.Call) -> CallNode:
        callee = self.visit(node.func)
        arguments = self._visit_list(node.args)

        children = []
        if callee:
            children.append(callee)
        children.extend(arguments)

        for kw in node.keywords:
            kw_val = self.visit(kw.value)
            if kw_val:
                children.append(kw_val)

        sem_node = CallNode(children=children, callee=callee, arguments=arguments)
        return self._attach_provenance(node, sem_node, *children)

    def visit_Return(self, node: ast.Return) -> ReturnNode:
        value = self.visit(node.value) if node.value else None
        children = [value] if value else []

        sem_node = ReturnNode(children=children, value=value)
        return self._attach_provenance(node, sem_node, *children)

    def visit_If(self, node: ast.If) -> IfNode:
        test = self.visit(node.test)
        body = self._visit_list(node.body)
        orelse = self._visit_list(node.orelse)

        children = []
        if test:
            children.append(test)
        children.extend(body)
        children.extend(orelse)

        sem_node = IfNode(children=children, test=test, body=body, orelse=orelse)
        return self._attach_provenance(node, sem_node, *children)

    def visit_For(self, node: ast.For) -> ForNode:
        target = self.visit(node.target)
        iterator = self.visit(node.iter)
        body = self._visit_list(node.body)
        orelse = self._visit_list(node.orelse)

        children = []
        if target:
            children.append(target)
        if iterator:
            children.append(iterator)
        children.extend(body)
        children.extend(orelse)

        sem_node = ForNode(children=children, target=target, iter=iterator, body=body, orelse=orelse)
        return self._attach_provenance(node, sem_node, *children)

    def visit_While(self, node: ast.While) -> WhileNode:
        test = self.visit(node.test)
        body = self._visit_list(node.body)
        orelse = self._visit_list(node.orelse)

        children = []
        if test:
            children.append(test)
        children.extend(body)
        children.extend(orelse)

        sem_node = WhileNode(children=children, test=test, body=body, orelse=orelse)
        return self._attach_provenance(node, sem_node, *children)


# Maintain alias for backward compatibility if needed
PythonSemanticASTBuilder = SemanticBuilder
