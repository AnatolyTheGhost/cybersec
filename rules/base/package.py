"""
RulePackage data model for grouping rules into domain packs.
"""

from dataclasses import dataclass, field
from typing import Type

from rules.base.rule import BaseRule


@dataclass(frozen=True)
class RulePackage:
    """
    Metadata and container for a rule package.

    Attributes
    ----------
    id:
        Unique identifier of the rule package.
    name:
        Human-readable name of the package.
    version:
        Semantic version string.
    description:
        Detailed summary of what the rule package covers.
    rules:
        List of rule classes included in this package.
    """

    id: str
    name: str
    version: str
    description: str = ""
    rules: list[Type[BaseRule]] = field(default_factory=list)
