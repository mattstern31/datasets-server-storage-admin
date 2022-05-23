import enum
import logging
import types
from datetime import datetime
from typing import Generic, List, Optional, Tuple, Type, TypedDict, TypeVar

from mongoengine import Document, DoesNotExist, connect
from mongoengine.fields import DateTimeField, EnumField, StringField
from mongoengine.queryset.queryset import QuerySet

# START monkey patching ### hack ###
# see https://github.com/sbdchd/mongo-types#install
U = TypeVar("U", bound=Document)


def no_op(self, x):  # type: ignore
    return self


QuerySet.__class_getitem__ = types.MethodType(no_op, QuerySet)


class QuerySetManager(Generic[U]):
    def __get__(self, instance: object, cls: Type[U]) -> QuerySet[U]:
        return QuerySet(cls, cls._get_collection())


# END monkey patching ### hack ###

logger = logging.getLogger(__name__)


class Status(enum.Enum):
    WAITING = "waiting"
    STARTED = "started"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class JobDict(TypedDict):
    status: str
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class DatasetJobDict(JobDict):
    dataset_name: str


class SplitJobDict(JobDict):
    dataset_name: str
    config_name: str
    split_name: str


class CountByStatus(TypedDict):
    waiting: int
    started: int
    success: int
    error: int
    cancelled: int


# All the fields are optional
class DumpByStatus(TypedDict, total=False):
    waiting: List[JobDict]
    started: List[JobDict]
    success: List[JobDict]
    error: List[JobDict]
    cancelled: List[JobDict]


def connect_to_queue(database, host) -> None:
    connect(database, alias="queue", host=host)


# States:
# - waiting: started_at is None and finished_at is None: waiting jobs
# - started: started_at is not None and finished_at is None: started jobs
# - finished: started_at is not None and finished_at is not None: finished jobs
# - cancelled: cancelled_at is not None: cancelled jobs
# For a given dataset_name, any number of finished and cancelled jobs are allowed,
# but only 0 or 1 job for the set of the other states
class DatasetJob(Document):
    meta = {"collection": "dataset_jobs", "db_alias": "queue"}
    dataset_name = StringField(required=True)
    created_at = DateTimeField(required=True)
    started_at = DateTimeField()
    finished_at = DateTimeField()
    status = EnumField(Status, default=Status.WAITING)

    def to_dict(self) -> DatasetJobDict:
        return {
            "dataset_name": self.dataset_name,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    def to_id(self) -> str:
        return f"DatasetJob[{self.dataset_name}]"

    objects = QuerySetManager["DatasetJob"]()


class SplitJob(Document):
    meta = {"collection": "split_jobs", "db_alias": "queue"}
    dataset_name = StringField(required=True)
    config_name = StringField(required=True)
    split_name = StringField(required=True)
    status = EnumField(Status, default=Status.WAITING)
    created_at = DateTimeField(required=True)
    started_at = DateTimeField()
    finished_at = DateTimeField()

    def to_dict(self) -> SplitJobDict:
        return {
            "dataset_name": self.dataset_name,
            "config_name": self.config_name,
            "split_name": self.split_name,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    def to_id(self) -> str:
        return f"SplitJob[{self.dataset_name}, {self.config_name}, {self.split_name}]"

    objects = QuerySetManager["SplitJob"]()


AnyJob = TypeVar("AnyJob", DatasetJob, SplitJob)  # Must be DatasetJob or SplitJob


# TODO: add priority (webhook: 5, warming: 3, refresh: 1)
# TODO: add status (valid/error/stalled) to the finished jobs
# TODO: limit the size of the queue? remove the oldest if room is needed?
# TODO: how to avoid deadlocks (a worker has taken the job, but never finished)? stalled, hours

# enqueue
# dequeue
# peek
# is full
# is empty


class EmptyQueue(Exception):
    pass


class JobNotFound(Exception):
    pass


def add_job(existing_jobs: QuerySet[AnyJob], new_job: AnyJob):
    try:
        # Check if a non-finished job already exists
        existing_jobs.filter(status__in=[Status.WAITING, Status.STARTED]).get()
    except DoesNotExist:
        new_job.save()
    # raises MultipleObjectsReturned if more than one entry -> should never occur, we let it raise


def add_dataset_job(dataset_name: str) -> None:
    add_job(
        DatasetJob.objects(dataset_name=dataset_name),
        DatasetJob(dataset_name=dataset_name, created_at=datetime.utcnow(), status=Status.WAITING),
    )


def add_split_job(dataset_name: str, config_name: str, split_name: str) -> None:
    add_job(
        SplitJob.objects(dataset_name=dataset_name, config_name=config_name, split_name=split_name),
        SplitJob(
            dataset_name=dataset_name,
            config_name=config_name,
            split_name=split_name,
            created_at=datetime.utcnow(),
            status=Status.WAITING,
        ),
    )


def get_jobs_with_status(jobs: QuerySet[AnyJob], status: Status) -> QuerySet[AnyJob]:
    return jobs(status=status)


def get_waiting(jobs: QuerySet[AnyJob]) -> QuerySet[AnyJob]:
    return get_jobs_with_status(jobs, Status.WAITING)


def get_started(jobs: QuerySet[AnyJob]) -> QuerySet[AnyJob]:
    return get_jobs_with_status(jobs, Status.STARTED)


def get_num_started_for_dataset(jobs: QuerySet[AnyJob], dataset_name: str) -> int:
    return jobs(status=Status.STARTED, dataset_name=dataset_name).count()


def get_finished(jobs: QuerySet[AnyJob]) -> QuerySet[AnyJob]:
    return jobs(status__nin=[Status.WAITING, Status.STARTED])


def get_excluded_dataset_names(jobs: QuerySet[AnyJob], max_jobs_per_dataset: Optional[int] = None) -> List[str]:
    if max_jobs_per_dataset is None:
        return []
    dataset_names = [job.dataset_name for job in jobs(status=Status.STARTED).only("dataset_name")]
    return list(
        {dataset_name for dataset_name in dataset_names if dataset_names.count(dataset_name) >= max_jobs_per_dataset}
    )


def start_job(jobs: QuerySet[AnyJob], max_jobs_per_dataset: Optional[int] = None) -> AnyJob:
    excluded_dataset_names = get_excluded_dataset_names(jobs, max_jobs_per_dataset)
    next_waiting_job = (
        jobs(status=Status.WAITING, dataset_name__nin=excluded_dataset_names)
        .order_by("+created_at")
        .no_cache()
        .first()
    )
    # ^ no_cache should generate a query on every iteration, which should solve concurrency issues between workers
    if next_waiting_job is None:
        raise EmptyQueue("no job available (within the limit of {max_jobs_per_dataset} started jobs per dataset)")
    next_waiting_job.update(started_at=datetime.utcnow(), status=Status.STARTED)
    return next_waiting_job


def get_dataset_job(max_jobs_per_dataset: Optional[int] = None) -> Tuple[str, str]:
    job = start_job(DatasetJob.objects, max_jobs_per_dataset)
    # ^ max_jobs_per_dataset is not very useful for the DatasetJob queue
    # since only one job per dataset can exist anyway
    # It's here for consistency and safeguard
    return str(job.pk), job.dataset_name
    # ^ job.pk is the id. job.id is not recognized by mypy


def get_split_job(max_jobs_per_dataset: Optional[int] = None) -> Tuple[str, str, str, str]:
    job = start_job(SplitJob.objects, max_jobs_per_dataset)
    return str(job.pk), job.dataset_name, job.config_name, job.split_name
    # ^ job.pk is the id. job.id is not recognized by mypy


def finish_started_job(jobs: QuerySet[AnyJob], job_id: str, success: bool) -> None:
    try:
        job = jobs(pk=job_id).get()
    except DoesNotExist:
        logger.error(f"started job {job_id} does not exist. Aborting.")
        return
    if job.status is not Status.STARTED:
        logger.warning(
            f"started job {job.to_id()} has a not the STARTED status ({job.status.value}). Force finishing anyway."
        )
    if job.finished_at is not None:
        logger.warning(f"started job {job.to_id()} has a non-empty finished_at field. Force finishing anyway.")
    if job.started_at is None:
        logger.warning(f"started job {job.to_id()} has an empty started_at field. Force finishing anyway.")
    status = Status.SUCCESS if success else Status.ERROR
    job.update(finished_at=datetime.utcnow(), status=status)


def finish_dataset_job(job_id: str, success: bool) -> None:
    finish_started_job(DatasetJob.objects, job_id, success)


def finish_split_job(job_id: str, success: bool) -> None:
    finish_started_job(SplitJob.objects, job_id, success)


def clean_database() -> None:
    DatasetJob.drop_collection()  # type: ignore
    SplitJob.drop_collection()  # type: ignore


def cancel_started_dataset_jobs() -> None:
    for job in get_started(DatasetJob.objects):
        job.update(finished_at=datetime.utcnow(), status=Status.CANCELLED)
        add_dataset_job(dataset_name=job.dataset_name)


def cancel_started_split_jobs() -> None:
    for job in get_started(SplitJob.objects):
        job.update(finished_at=datetime.utcnow(), status=Status.CANCELLED)
        add_split_job(dataset_name=job.dataset_name, config_name=job.config_name, split_name=job.split_name)


# special reports


def get_jobs_count_by_status(jobs: QuerySet[AnyJob]) -> CountByStatus:
    return {
        "waiting": get_jobs_with_status(jobs, Status.WAITING).count(),
        "started": get_jobs_with_status(jobs, Status.STARTED).count(),
        "success": get_jobs_with_status(jobs, Status.SUCCESS).count(),
        "error": get_jobs_with_status(jobs, Status.ERROR).count(),
        "cancelled": get_jobs_with_status(jobs, Status.CANCELLED).count(),
    }


def get_dataset_jobs_count_by_status() -> CountByStatus:
    return get_jobs_count_by_status(DatasetJob.objects)


def get_split_jobs_count_by_status() -> CountByStatus:
    return get_jobs_count_by_status(SplitJob.objects)


def get_dump_with_status(jobs: QuerySet[AnyJob], status: Status) -> List[JobDict]:
    return [d.to_dict() for d in get_jobs_with_status(jobs, status)]


def get_dump_by_status(jobs: QuerySet[AnyJob], waiting_started: bool = False) -> DumpByStatus:
    if waiting_started:
        return {
            "waiting": get_dump_with_status(jobs, Status.WAITING),
            "started": get_dump_with_status(jobs, Status.STARTED),
        }
    return {
        "waiting": get_dump_with_status(jobs, Status.WAITING),
        "started": get_dump_with_status(jobs, Status.STARTED),
        "success": get_dump_with_status(jobs, Status.SUCCESS),
        "error": get_dump_with_status(jobs, Status.ERROR),
        "cancelled": get_dump_with_status(jobs, Status.CANCELLED),
    }


def get_dataset_dump_by_status(waiting_started: bool = False) -> DumpByStatus:
    return get_dump_by_status(DatasetJob.objects, waiting_started)


def get_split_dump_by_status(waiting_started: bool = False) -> DumpByStatus:
    return get_dump_by_status(SplitJob.objects, waiting_started)


def is_dataset_in_queue(dataset_name: str) -> bool:
    return DatasetJob.objects(status__in=[Status.WAITING, Status.STARTED], dataset_name=dataset_name).count() > 0


def is_split_in_queue(dataset_name: str, config_name: str, split_name: str) -> bool:
    return (
        SplitJob.objects(
            status__in=[Status.WAITING, Status.STARTED],
            dataset_name=dataset_name,
            config_name=config_name,
            split_name=split_name,
        ).count()
        > 0
    )