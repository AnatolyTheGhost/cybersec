import json
from typing import Any, Dict
from modules.semantic_ast.nodes import SemanticNode, SourceRange

def source_range_to_dict(sr: SourceRange) -> Dict[str, int]:
    if sr is None:
        return {}
    return {
        "start_line": sr.start_line,
        "start_column": sr.start_column,
        "end_line": sr.end_line,
        "end_column": sr.end_column,
    }

def node_to_dict(node: SemanticNode) -> Dict[str, Any]:
    if not isinstance(node, SemanticNode):
        return {}
    
    # Base fields
    res = {
        "id": node.id,
        "kind": node.kind,
        "language": node.language,
        "source_range": source_range_to_dict(node.source_range) if node.source_range else None,
        "source_ast_ids": sorted(str(item) for item in node.source_ast_ids),
        "attributes": node.attributes,
    }
    
    ignored_attrs = {"id", "source_range", "source_ast_ids", "children", "language", "attributes", "kind"}
    for attr, val in node.__dict__.items():
        if attr in ignored_attrs:
            continue
        if isinstance(val, SemanticNode):
            res[attr] = node_to_dict(val)
        elif isinstance(val, list):
            res[attr] = [node_to_dict(item) if isinstance(item, SemanticNode) else item for item in val]
        else:
            res[attr] = val
            
    res["children"] = [node_to_dict(child) for child in node.children]
    return res


def to_json(node: SemanticNode, indent: int = 2) -> str:
    """
    Serializes a SemanticAST node and its subtree to a JSON string.
    """
    return json.dumps(node_to_dict(node), indent=indent)


def to_pretty_string(node: SemanticNode, indent: int = 0) -> str:
    """
    Returns a human-readable text representation of the Semantic AST.
    """
    indent_str = "  " * indent
    lines = []
    
    props = []
    for attr in ["name", "value", "module_name", "names", "bases"]:
        if hasattr(node, attr) and getattr(node, attr) is not None:
            val = getattr(node, attr)
            if val != "" and val != []:
                props.append(f"{attr}={repr(val)}")
                
    if node.source_range:
        sr = node.source_range
        props.append(f"loc={sr.start_line}:{sr.start_column}-{sr.end_line}:{sr.end_column}")
        
    prop_suffix = f" ({', '.join(props)})" if props else ""
    lines.append(f"{indent_str}{node.kind}{prop_suffix}")
    
    for child in node.children:
        lines.append(to_pretty_string(child, indent + 1))
        
    return "\n".join(lines)
