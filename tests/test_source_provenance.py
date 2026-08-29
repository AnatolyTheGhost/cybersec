import ast

from engine.domain.finding import Finding, FindingKind, Severity, SourceRange
from modules.ast.parser import ASTParser
from modules.semantic_ast.builder import SemanticBuilder


def test_ast_parser_attaches_ids_and_source_ranges():
    tree = ASTParser().parse("value = 1\n")
    assign_node = next(node for node in ast.walk(tree) if isinstance(node, ast.Assign))

    assert getattr(assign_node, "id", None) is not None
    assert getattr(assign_node, "source_range", None) is not None
    assert assign_node.source_range.file == "<unknown>"
    assert assign_node.source_range.start_line == 1
    assert assign_node.source_range.start_column == 0
    assert assign_node.source_range.end_line == 1


def test_semantic_builder_propagates_source_location_and_ast_ids():
    tree = ASTParser().parse("value = 1\n",)
    module = SemanticBuilder().build(tree, filename="sample.py")

    assignment = module.children[0]
    assert assignment.source_range is not None
    assert assignment.source_range.file == "sample.py"
    assert assignment.source_ast_ids
    assert assignment.value is not None
    assert assignment.value.source_range is not None
    assert assignment.value.source_ast_ids <= assignment.source_ast_ids


def test_finding_serializes_location_in_nested_shape():
    finding = Finding(
        id="finding-1",
        kind=FindingKind.INJECTION,
        severity=Severity.HIGH,
        location=SourceRange(
            file="app.py",
            start_line=3,
            start_column=4,
            end_line=5,
            end_column=9,
        ),
        rule_id="injection.sql",
        confidence=0.9,
        message="Unsafe query",
    )

    payload = finding.to_dict()
    assert payload["location"]["file"] == "app.py"
    assert payload["location"]["start"] == {"line": 3, "column": 4}
    assert payload["location"]["end"] == {"line": 5, "column": 9}
