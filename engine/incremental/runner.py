"""Domain contract for one incremental analysis execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TypeAlias
from uuid import UUID, uuid4

from .mutations import BatchId, VersionId


RunId: TypeAlias = UUID


class IncrementalRunMode(str, Enum):
    """The analysis mode represented by this run contract."""

    INCREMENTAL = "incremental"


class IncrementalRunStatus(str, Enum):
    """Lifecycle snapshots for one incremental analysis execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class IncrementalRun:
    """Immutable snapshot connecting one MutationBatch to a version transition.

    This is not a user-facing ScanSession and contains neither artifacts nor
    analysis logic.  A coordinator can create successive snapshots as the
    run progresses from pending to a terminal status.
    """

    batch_id: BatchId
    input_version_id: VersionId
    status: IncrementalRunStatus = IncrementalRunStatus.PENDING
    output_version_id: VersionId | None = None
    mode: IncrementalRunMode = IncrementalRunMode.INCREMENTAL
    run_id: RunId = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, UUID):
            raise TypeError("run_id must be a UUID")
        if not isinstance(self.batch_id, UUID):
            raise TypeError("batch_id must be a UUID")
        if not isinstance(self.input_version_id, str) or not self.input_version_id.strip():
            raise ValueError("input_version_id is required")
        if not isinstance(self.status, IncrementalRunStatus):
            raise TypeError("status must be an IncrementalRunStatus")
        if not isinstance(self.mode, IncrementalRunMode):
            raise TypeError("mode must be an IncrementalRunMode")
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")

        if self.status is IncrementalRunStatus.FAILED and self.output_version_id is not None:
            raise ValueError("a failed run must not publish output_version_id")

        if self.output_version_id is not None:
            if not isinstance(self.output_version_id, str) or not self.output_version_id.strip():
                raise ValueError("output_version_id must be a non-empty string")
            if self.status is not IncrementalRunStatus.COMPLETED:
                raise ValueError("output_version_id is only valid for a completed run")
        elif self.status is IncrementalRunStatus.COMPLETED:
            raise ValueError("a completed run must publish output_version_id")

        self._validate_timestamp("started_at", self.started_at)
        self._validate_timestamp("finished_at", self.finished_at)
        if self.started_at is not None and self.started_at < self.created_at:
            raise ValueError("started_at cannot precede created_at")
        if self.finished_at is not None and self.finished_at < self.created_at:
            raise ValueError("finished_at cannot precede created_at")
        if self.started_at is not None and self.finished_at is not None and self.finished_at < self.started_at:
            raise ValueError("finished_at cannot precede started_at")

    @staticmethod
    def _validate_timestamp(name: str, value: datetime | None) -> None:
        if value is not None and not isinstance(value, datetime):
            raise TypeError(f"{name} must be a datetime")
