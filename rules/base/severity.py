"""
Severity enumeration for rule findings.
"""

from enum import Enum


class Severity(str, Enum):
    """
    Severity levels for rule findings.
    """
    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
