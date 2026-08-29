import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from modules.ast.nodes import SourceRange


@dataclass
class SemanticNode:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    source_range: Optional[SourceRange] = None
    source_ast_ids: set[uuid.UUID] = field(default_factory=set)
    children: List["SemanticNode"] = field(default_factory=list)
    language: str = "python"
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def kind(self) -> str:
        name = self.__class__.__name__
        if name.endswith("Node"):
            return name[:-4]
        return name


@dataclass
class ModuleNode(SemanticNode):
    name: Optional[str] = None
    docstring: Optional[str] = None


@dataclass
class ImportNode(SemanticNode):
    module_name: str = ""
    names: List[str] = field(default_factory=list)


@dataclass
class ClassNode(SemanticNode):
    name: str = ""
    bases: List[str] = field(default_factory=list)


@dataclass
class FunctionNode(SemanticNode):
    name: str = ""
    parameters: List["ParameterNode"] = field(default_factory=list)
    is_method: bool = False


@dataclass
class ParameterNode(SemanticNode):
    name: str = ""
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None


@dataclass
class VariableNode(SemanticNode):
    name: str = ""
    type_annotation: Optional[str] = None


@dataclass
class AssignmentNode(SemanticNode):
    targets: List[SemanticNode] = field(default_factory=list)
    value: Optional[SemanticNode] = None


@dataclass
class CallNode(SemanticNode):
    callee: Optional[SemanticNode] = None
    arguments: List[SemanticNode] = field(default_factory=list)


@dataclass
class ReturnNode(SemanticNode):
    value: Optional[SemanticNode] = None


@dataclass
class IfNode(SemanticNode):
    test: Optional[SemanticNode] = None
    body: List[SemanticNode] = field(default_factory=list)
    orelse: List[SemanticNode] = field(default_factory=list)


@dataclass
class ForNode(SemanticNode):
    target: Optional[SemanticNode] = None
    iter: Optional[SemanticNode] = None
    body: List[SemanticNode] = field(default_factory=list)
    orelse: List[SemanticNode] = field(default_factory=list)


@dataclass
class WhileNode(SemanticNode):
    test: Optional[SemanticNode] = None
    body: List[SemanticNode] = field(default_factory=list)
    orelse: List[SemanticNode] = field(default_factory=list)


@dataclass
class LiteralNode(SemanticNode):
    value: Any = None


@dataclass
class IdentifierNode(SemanticNode):
    name: str = ""
