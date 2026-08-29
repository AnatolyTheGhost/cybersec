"""
Base abstract class for all static analysis security rules.
"""

from abc import ABC, abstractmethod
from typing import Any

from rules.base.finding import Finding
from rules.base.severity import Severity


class BaseRule(ABC):
    """
    Abstract Base Class for analysis rules.
    """

    id: str
    name: str
    description: str
    severity: Severity | str
    confidence: float

    @abstractmethod
    def analyze(self, context: Any) -> list[Finding]:
        """
        Execute analysis on the provided context.

        Parameters
        ----------
        context:
            The analysis context containing AST, metadata, or source code.

        Returns
        -------
        list[Finding]
            List of findings detected by this rule.
        """
        pass
