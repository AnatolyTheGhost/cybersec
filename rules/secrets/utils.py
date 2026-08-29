"""Shared helpers for secret-rule semantic AST traversal and detection."""

import re
from typing import Any, Iterable, Optional

from modules.semantic_ast.nodes import (
    AssignmentNode,
    IdentifierNode,
    LiteralNode,
    SemanticNode,
    VariableNode,
)


def iter_nodes(node: SemanticNode) -> Iterable[SemanticNode]:
    yield node
    for child in getattr(node, "children", []):
        yield from iter_nodes(child)
    if isinstance(node, AssignmentNode):
        for target in node.targets:
            yield from iter_nodes(target)
        if node.value is not None:
            yield from iter_nodes(node.value)


def extract_string(node: SemanticNode) -> Optional[str]:
    if isinstance(node, LiteralNode) and isinstance(node.value, str):
        return node.value
    return None


def get_target_name(node: SemanticNode) -> Optional[str]:
    if isinstance(node, (IdentifierNode, VariableNode)):
        return node.name.lower()
    return None


def node_line(node: SemanticNode) -> int:
    if node.source_range is not None and node.source_range.start_line is not None:
        return node.source_range.start_line
    return 1


def iter_assignments(node: SemanticNode) -> Iterable[AssignmentNode]:
    if isinstance(node, AssignmentNode):
        yield node
    for child in getattr(node, "children", []):
        yield from iter_assignments(child)
    if isinstance(node, AssignmentNode):
        for target in node.targets:
            yield from iter_assignments(target)
        if node.value is not None:
            yield from iter_assignments(node.value)


def iter_literals(node: SemanticNode) -> Iterable[LiteralNode]:
    if isinstance(node, LiteralNode):
        yield node
    for child in getattr(node, "children", []):
        yield from iter_literals(child)
    if isinstance(node, AssignmentNode):
        for target in node.targets:
            yield from iter_literals(target)
        if node.value is not None:
            yield from iter_literals(node.value)


def normalize_value(value: str) -> str:
    return value.strip()


def is_secret_like_value(value: str) -> bool:
    return bool(value and not value.isspace())


def has_path_like_dotenv(value: str) -> bool:
    return value.strip() == ".env" or value.strip().endswith(".env")


def regex_search(pattern: str, value: str) -> bool:
    return bool(re.search(pattern, value, re.IGNORECASE | re.DOTALL))
