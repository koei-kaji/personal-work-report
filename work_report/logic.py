from datetime import date, datetime
from typing import Final, List

from pony.orm import db_session
from pony.orm.core import TransactionIntegrityError

from . import view_models
from .database import models

# register >  update > delete > acquire-many > acquire-one


class LogicException(Exception):
    pass


class Category:
    @staticmethod
    def register(name: str) -> None:
        """Register a category

        Args:
            name (str): Category name

        Raises:
            LogicException: Occurs when trying to register same category name
        """
        try:
            with db_session(serializable=True, strict=True):
                models.Category.insert(name)
        except TransactionIntegrityError as error:
            raise LogicException from error

    @staticmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def acquire_all() -> List[view_models.Category]:
        """Acquire all categories and convert to view model

        Returns:
            List[view_models.Category]: All categories
        """

        db_categories = models.Category.select_all()

        return [
            view_models.Category.from_orm(db_category) for db_category in db_categories
        ]


class Job:
    @staticmethod
    def register(job_name: str, category_name: str | None = None) -> None:
        """Register a job.

        Args:
            job_name (str): Job name
            category_name (str | None): Category name

        Raises:
            LogicException:
                - Occurs when trying to register same combination of job name and category name.
                - Occurs when category is specified but not found in the database.
        """

        try:
            with db_session(serializable=True, strict=True):
                if category_name is None:
                    models.Job.insert(job_name, None)
                    return

                db_category = models.Category.select_one_by_name(category_name)
                if db_category is None:
                    raise LogicException("Category is specified, but not found.")
                models.Job.insert(job_name, db_category)

        except (TransactionIntegrityError, models.CRUDException) as error:
            raise LogicException(error) from error

    @staticmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def acquire_all() -> List[view_models.Job]:
        """Acquire all jobs and convert to view model

        Returns:
            List[view_models.Job]: All jobs
        """

        db_jobs = models.Job.select_all()
        return [view_models.Job.from_orm(db_job) for db_job in db_jobs]


class JobRecord:
    @classmethod
    def __replace_second_0(cls, __datetime: datetime) -> datetime:
        """Set second and microsecond to 0.

        Args:
            __datetime (datetime): Datetime

        Returns:
            datetime: Datetime
        """
        return __datetime.replace(second=0, microsecond=0)

    @classmethod
    def __judge_if_can_upsert_and_get_job(
        cls, job_id: int, start: datetime, end: datetime | None = None
    ) -> models.Job:
        """Judge if job record can be upcert and returns the job if so.

        This private function must be used inside db_session.

        Args:
            job_id (int): Job id
            start (datetime): Start time
            end (datetime | None, optional): End time

        Raises:
            LogicException:  Occurs when future time is set for start datetime or end datetime.
            LogicException:  Occurs when job specified job id cannot be found.
            LogicException:  Occurs when end datetime is smaller than equal to start datetime.
            LogicException:  Occurs when start and end are not same dates.

        Returns:
            models.Job: Job
        """
        # TODO: 登録期間で重なりがないかの検証を加える
        CURRENT_DATETIME: Final[datetime] = datetime.now()
        if start > CURRENT_DATETIME:
            raise LogicException("Start time cannot be set at future time.")

        db_job = models.Job.select_one_by_id(job_id)
        if db_job is None:
            raise LogicException(f"Job(id={job_id}) cannot be found.")

        if end is not None:
            if end > CURRENT_DATETIME:
                raise LogicException("End time cannot be set at future time.")
            if end <= start:
                raise LogicException("End time must be greater than start time.")
            if start.date() != end.date():
                raise LogicException("Start and end must be same dates.")

        return db_job

    @classmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def register(cls, job_id: int, start: datetime, end: datetime) -> None:
        """Register a job record.

        Args:
            job_id (int): Job ID
            start (datetime): Start datetime
            end (datetime): End datetime

        Raises:
            LogicException: See __judge_if_can_upcert_and_get_job()
        """
        # TODO: マルチタスクを禁止するため、start - endの時間で重なりがあるものがあればその旨をエラーにする。

        start = cls.__replace_second_0(start)
        end = cls.__replace_second_0(end)
        db_job = cls.__judge_if_can_upsert_and_get_job(job_id, start, end)
        models.JobRecord.insert(db_job, start, end)

    @classmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def revise(
        cls, job_record_id: int, job_id: int, start: datetime, end: datetime
    ) -> None:
        """Revise the job record specified by id.

        Args:
            job_record_id (int): Job record id
            job_id (int): Job id
            start (datetime): Start datetime
            end (datetime): End datetime

        Raises:
            LogicException: Occurs when job record specified job id cannot be found.
            LogicException: See __judge_if_can_upcert_and_get_job()
        """
        # TODO: 終了したジョブを開始するのに変更できるようにendでnullableを許容する

        db_job_record = models.JobRecord.select_one_by_id(job_record_id)
        if db_job_record is None:
            raise LogicException(f"JobRecord(id={job_record_id}) cannot be found")

        start = cls.__replace_second_0(start)
        end = cls.__replace_second_0(end)
        db_job = JobRecord.__judge_if_can_upsert_and_get_job(job_id, start, end)
        models.JobRecord.update(db_job_record, db_job, start, end)

    @classmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def start(cls, job_id: int) -> None:
        """Start a job record specified by job id.

        Args:
            job_id (int): Job id

        Raises:
            LogicException: Occurs when one job has been already started.
            LogicException: See __judge_if_can_upsert_and_get_job()
        """
        current_datetime = datetime.now()
        job_record_in_progress = models.JobRecord.select_one_in_progress_by_date(
            current_datetime.date()
        )
        if job_record_in_progress is not None:
            raise LogicException(
                f"JobRecord(id={job_record_in_progress.id}) is already started."
            )

        start = cls.__replace_second_0(datetime.now())
        db_job = cls.__judge_if_can_upsert_and_get_job(job_id, start)
        models.JobRecord.insert(db_job, start)

    @classmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def stop(cls, job_record_id: int) -> None:
        """Stop a job record specified by job record id.

        Args:
            job_record_id (int): Job record id

        Raises:
            LogicException: Occurs when job record specified job id cannot be found.
            LogicException: Occurs when the job was already stopped.
        """

        current_datetime = datetime.now()
        db_job_record = models.JobRecord.select_one_by_id(job_record_id)
        if db_job_record is None:
            raise LogicException(f"JobRecord(id={job_record_id}) cannot be found.")
        if db_job_record.end is not None:
            raise LogicException(f"JobRecord(id={job_record_id}) is already stopped.")

        models.JobRecord.update_end(db_job_record, current_datetime)

    # TODO: docstring
    @classmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def acquire_all_finished_by_date(cls, __date: date) -> List[view_models.JobRecord]:
        db_job_records = models.JobRecord.select_all_finished_by_date(__date)
        return [
            view_models.JobRecord.from_orm(db_job_record)
            for db_job_record in db_job_records
        ]

    # TODO: docstring
    @classmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def acquire_one_in_progress_by_date(
        cls, __date: date
    ) -> view_models.JobRecord | None:
        db_job_record = models.JobRecord.select_one_in_progress_by_date(__date)
        if db_job_record is None:
            return None

        return view_models.JobRecord.from_orm(db_job_record)


class Note:
    # TODO: docstring
    @classmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def save(cls, __date: date, content: str) -> None:
        models.Note.upsert(__date, content)

    # TODO: docstring
    @classmethod
    @db_session(serializable=True, strict=True)  # type: ignore[misc]
    def acquire_one_by_date(cls, __date: date) -> view_models.Note | None:
        db_note = models.Note.select_one_by_date(__date)
        if db_note is None:
            return None

        return view_models.Note.from_orm(db_note)
