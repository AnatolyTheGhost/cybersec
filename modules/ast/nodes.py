from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceRange:
    file: str = "<unknown>"
    start_line: int = 1
    start_column: int = 0
    end_line: int = 1
    end_column: int = 0

    def __post_init__(self) -> None:
        if self.start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {self.start_line}")
        if self.end_line < self.start_line:
            raise ValueError(
                f"end_line ({self.end_line}) must be >= start_line ({self.start_line})"
            )
        if self.start_column < 0 or self.end_column < 0:
            raise ValueError("columns must be >= 0")


class Node:
    def __init__(self, node_type: str, raw, source_range: SourceRange | None = None):
        self.type = node_type
        self.raw = raw
        self.children = []
        self.source_range = source_range
        self.id = None

    def add_child(self, node: "Node"):
        self.children.append(node)