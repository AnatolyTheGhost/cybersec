from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from engine.incremental.runner import (
    IncrementalRun,
    IncrementalRunMode,
    IncrementalRunStatus,
)


def test_pending_run_connects_one_batch_to_its_input_version():
    batch_id = uuid4()

    run = IncrementalRun(batch_id=batch_id, input_version_id="project-v1")

    assert isinstance(run.run_id, UUID)
    assert run.batch_id == batch_id
    assert run.input_version_id == "project-v1"
    assert run.output_version_id is None
    assert run.mode is IncrementalRunMode.INCREMENTAL
    assert run.status is IncrementalRunStatus.PENDING


def test_completed_run_publishes_output_version_after_commit():
    created_at = datetime(2026, 8, 18, tzinfo=timezone.utc)

    run = IncrementalRun(
        batch_id=uuid4(),
        input_version_id="project-v1",
        output_version_id="project-v2",
        status=IncrementalRunStatus.COMPLETED,
        created_at=created_at,
        started_at=created_at + timedelta(seconds=1),
        finished_at=created_at + timedelta(seconds=2),
    )

    assert run.output_version_id == "project-v2"
    assert run.finished_at is not None


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"batch_id": "not-a-uuid"}, "batch_id must be a UUID"),
        ({"input_version_id": ""}, "input_version_id is required"),
        ({"output_version_id": "project-v2"}, "only valid for a completed run"),
        ({"status": IncrementalRunStatus.COMPLETED}, "must publish output_version_id"),
        ({"status": IncrementalRunStatus.FAILED, "output_version_id": "project-v2"}, "failed run must not publish"),
    ],
)
def test_run_invariants(kwargs, message):
    defaults = {"batch_id": uuid4(), "input_version_id": "project-v1"}

    with pytest.raises((TypeError, ValueError), match=message):
        IncrementalRun(**(defaults | kwargs))


def test_run_is_an_immutable_state_snapshot():
    run = IncrementalRun(batch_id=uuid4(), input_version_id="project-v1")

    with pytest.raises(FrozenInstanceError):
        run.status = IncrementalRunStatus.RUNNING
