"""Mutations receiver package."""

from .adapters import ClaudeCodeAdapter, FileWatcherAdapter, MutationAdapter, VSCodeAdapter
from .backend_client import BackendClient
from .events import MutationEvent
from .receiver import MutationsReceiver
from .registry import AdapterRegistry
from .scan import FindingResult, ScanError, ScanResult, SourceRangeResult, scan_repository

__all__ = [
    # Adapters & events
    "AdapterRegistry",
    "BackendClient",
    "ClaudeCodeAdapter",
    "FileWatcherAdapter",
    "MutationAdapter",
    "MutationEvent",
    "MutationsReceiver",
    "VSCodeAdapter",
    # Repository scan entry point
    "scan_repository",
    "ScanResult",
    "ScanError",
    "FindingResult",
    "SourceRangeResult",
]
