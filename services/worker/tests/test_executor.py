import json
import os
import sys
import time
from datetime import timedelta
from pathlib import Path
from typing import Iterator
from unittest.mock import patch

import pytest
import pytz
from filelock import FileLock
from libcommon.queue import Job, JobInfo, Priority, Status, get_datetime
from libcommon.resources import QueueMongoResource
from mirakuru import ProcessExitedWithError, TimeoutExpired
from pytest import fixture

from worker.config import AppConfig
from worker.loop import WorkerState
from worker.main import WorkerExecutor


def get_job_info(prefix: str = "base") -> JobInfo:
    job_id = prefix.encode().hex()
    assert len(job_id) <= 24, "please choose a smaller prefix"
    return JobInfo(
        job_id=job_id + "0" * (24 - len(job_id)),
        type="bar",
        dataset=f"user/{prefix}_dataset",
        config="default",
        split="train",
        force=False,
        priority=Priority.LOW,
    )


def write_worker_state(worker_state: WorkerState, worker_state_path: str) -> None:
    with FileLock(worker_state_path + ".lock"):
        with open(worker_state_path, "w") as worker_state_f:
            json.dump(worker_state, worker_state_f)


def start_worker_loop() -> None:
    app_config = AppConfig.from_env()
    if not app_config.worker.state_path:
        raise ValueError("Failed to get worker state because WORKER_STATE_PATH is missing.")
    if "--print-worker-state-path" in sys.argv:
        print(app_config.worker.state_path, flush=True)
    current_job_info = get_job_info()
    worker_state = WorkerState(current_job_info=current_job_info)
    write_worker_state(worker_state, app_config.worker.state_path)


def start_worker_loop_that_crashes() -> None:
    app_config = AppConfig.from_env()
    if not app_config.worker.state_path:
        raise ValueError("Failed to get worker state because WORKER_STATE_PATH is missing.")
    if "--print-worker-state-path" in sys.argv:
        print(app_config.worker.state_path, flush=True)
    raise RuntimeError("Tried to run a bad worker loop")


def start_worker_loop_that_times_out() -> None:
    time.sleep(20)


@fixture
def set_worker_state(worker_state_path: Path) -> Iterator[WorkerState]:
    job_info = get_job_info()
    worker_state = WorkerState(current_job_info=job_info)
    write_worker_state(worker_state, str(worker_state_path))
    yield worker_state
    os.remove(worker_state_path)


@fixture
def set_just_started_job_in_queue(queue_mongo_resource: QueueMongoResource) -> Iterator[Job]:
    if not queue_mongo_resource.is_available():
        raise RuntimeError("Mongo resource is not available")
    job_info = get_job_info()
    if Job.objects.with_id(job_info["job_id"]):  # type: ignore
        Job.objects.with_id(job_info["job_id"]).delete()  # type: ignore
    created_at = get_datetime()
    job = Job(
        pk=job_info["job_id"],
        type=job_info["type"],
        dataset=job_info["dataset"],
        config=job_info["config"],
        split=job_info["split"],
        unicity_id="unicity_id",
        namespace="user",
        priority=job_info["priority"],
        status=Status.STARTED,
        created_at=created_at,
        started_at=created_at + timedelta(microseconds=1),
    )
    job.save()
    yield job
    job.delete()


@fixture
def set_long_running_job_in_queue(app_config: AppConfig, queue_mongo_resource: QueueMongoResource) -> Iterator[Job]:
    if not queue_mongo_resource.is_available():
        raise RuntimeError("Mongo resource is not available")
    job_info = get_job_info("long")
    if Job.objects.with_id(job_info["job_id"]):  # type: ignore
        Job.objects.with_id(job_info["job_id"]).delete()  # type: ignore
    created_at = get_datetime() - timedelta(days=1)
    last_heartbeat = get_datetime() - timedelta(seconds=app_config.worker.heartbeat_time_interval_seconds)
    job = Job(
        pk=job_info["job_id"],
        type=job_info["type"],
        dataset=job_info["dataset"],
        config=job_info["config"],
        split=job_info["split"],
        unicity_id="unicity_id",
        namespace="user",
        priority=job_info["priority"],
        status=Status.STARTED,
        created_at=created_at,
        started_at=created_at + timedelta(milliseconds=1),
        last_heartbeat=last_heartbeat,
    )
    job.save()
    yield job
    job.delete()


@fixture
def set_zombie_job_in_queue(queue_mongo_resource: QueueMongoResource) -> Iterator[Job]:
    if not queue_mongo_resource.is_available():
        raise RuntimeError("Mongo resource is not available")
    job_info = get_job_info("zombie")
    if Job.objects.with_id(job_info["job_id"]):  # type: ignore
        Job.objects.with_id(job_info["job_id"]).delete()  # type: ignore
    created_at = get_datetime() - timedelta(days=1)
    job = Job(
        pk=job_info["job_id"],
        type=job_info["type"],
        dataset=job_info["dataset"],
        config=job_info["config"],
        split=job_info["split"],
        unicity_id="unicity_id",
        namespace="user",
        priority=job_info["priority"],
        status=Status.STARTED,
        created_at=created_at,
        started_at=created_at + timedelta(milliseconds=1),
        last_heartbeat=created_at + timedelta(milliseconds=2),
    )
    job.save()
    yield job
    job.delete()


def test_executor_get_state(app_config: AppConfig, set_worker_state: WorkerState) -> None:
    executor = WorkerExecutor(app_config)
    assert executor.get_state() == set_worker_state


def test_executor_get_empty_state(app_config: AppConfig) -> None:
    executor = WorkerExecutor(app_config)
    assert executor.get_state() == WorkerState(current_job_info=None)


def test_executor_get_current_job(
    app_config: AppConfig, set_just_started_job_in_queue: Job, set_worker_state: WorkerState
) -> None:
    executor = WorkerExecutor(app_config)
    assert executor.get_current_job() == set_just_started_job_in_queue


def test_executor_get_nonexisting_current_job(app_config: AppConfig) -> None:
    executor = WorkerExecutor(app_config)
    assert executor.get_current_job() is None


def test_executor_get_zombies(
    app_config: AppConfig,
    set_just_started_job_in_queue: Job,
    set_long_running_job_in_queue: Job,
    set_zombie_job_in_queue: Job,
) -> None:
    zombie = set_zombie_job_in_queue
    executor = WorkerExecutor(app_config)
    assert executor.get_zombies() == [zombie]


def test_executor_heartbeat(
    app_config: AppConfig,
    set_just_started_job_in_queue: Job,
    set_worker_state: WorkerState,
) -> None:
    executor = WorkerExecutor(app_config)
    current_job = executor.get_current_job()
    assert current_job is not None
    assert current_job.last_heartbeat is None
    executor.heartbeat()
    current_job = executor.get_current_job()
    assert current_job is not None
    assert current_job.last_heartbeat is not None
    last_heartbeat_datetime = pytz.UTC.localize(current_job.last_heartbeat)
    assert last_heartbeat_datetime >= get_datetime() - timedelta(seconds=1)


def test_executor_kill_zombies(
    app_config: AppConfig,
    set_just_started_job_in_queue: Job,
    set_long_running_job_in_queue: Job,
    set_zombie_job_in_queue: Job,
) -> None:
    zombie = set_zombie_job_in_queue
    executor = WorkerExecutor(app_config)
    assert executor.get_zombies() == [zombie]
    executor.kill_zombies()
    assert executor.get_zombies() == []
    assert Job.objects.with_id(zombie.pk).status == Status.ERROR  # type: ignore


def test_executor_start(
    app_config: AppConfig,
    queue_mongo_resource: QueueMongoResource,
    set_just_started_job_in_queue: Job,
    set_zombie_job_in_queue: Job,
) -> None:
    if not queue_mongo_resource.is_available():
        raise RuntimeError("Mongo resource is not available")
    executor = WorkerExecutor(app_config)
    with patch.object(executor, "heartbeat", wraps=executor.heartbeat) as heartbeat_mock:
        with patch.object(executor, "kill_zombies", wraps=executor.kill_zombies) as kill_zombies_mock:
            with patch("worker.main.START_WORKER_LOOP_PATH", __file__):
                executor.start()
    current_job = executor.get_current_job()
    assert current_job is not None
    assert str(current_job.pk) == get_job_info()["job_id"]
    assert heartbeat_mock.call_count > 0
    assert Job.objects.with_id(set_just_started_job_in_queue.pk).last_heartbeat is not None  # type: ignore
    assert kill_zombies_mock.call_count > 0
    assert Job.objects.with_id(set_zombie_job_in_queue.pk).status == Status.ERROR  # type: ignore


@pytest.mark.parametrize(
    "bad_worker_loop_type", ["start_worker_loop_that_crashes", "start_worker_loop_that_times_out"]
)
def test_executor_raises_on_bad_worker(
    app_config: AppConfig, queue_mongo_resource: QueueMongoResource, tmp_path: Path, bad_worker_loop_type: str
) -> None:
    if not queue_mongo_resource.is_available():
        raise RuntimeError("Mongo resource is not available")
    bad_start_worker_loop_path = tmp_path / "bad_start_worker_loop.py"
    with bad_start_worker_loop_path.open("w") as bad_start_worker_loop_f:
        bad_start_worker_loop_f.write("raise RuntimeError('Tried to start a bad worker loop.')")
    executor = WorkerExecutor(app_config)
    with patch.dict(os.environ, {"WORKER_LOOP_TYPE": bad_worker_loop_type}):
        with patch("worker.main.START_WORKER_LOOP_PATH", __file__):
            with pytest.raises((ProcessExitedWithError, TimeoutExpired)):
                executor.start()


if __name__ == "__main__":
    worker_loop_type = os.environ.get("WORKER_LOOP_TYPE", "start_worker_loop")
    if worker_loop_type == "start_worker_loop_that_crashes":
        start_worker_loop_that_crashes()
    elif worker_loop_type == "start_worker_loop_that_times_out":
        start_worker_loop_that_times_out()
    else:
        start_worker_loop()
