from __future__ import annotations

from datetime import date, datetime
from typing import List, TypeAlias, cast

from pony.orm import (
    Database,
    LongStr,
    Optional,
    PrimaryKey,
    Required,
    Set,
    composite_key,
)
from pony.orm.core import CacheIndexError

from .database import DatabaseSingleton

Date: TypeAlias = date
DateTime: TypeAlias = datetime

db: Database = DatabaseSingleton.get_instance()


class CRUDException(Exception):
    pass


class DataAlreadyExistsError(CRUDException):
    def __init__(self, entity: db.Entity) -> None:
        message = f"{entity} is already exists."
        super().__init__(message)


class Category(db.Entity):  # type: ignore[misc]
    _table_ = "categories"
    name = PrimaryKey(str)
    jobs = Set("Job")

    @classmethod
    def insert(cls, name: str) -> None:
        """Insert a category to the database.

        Args:
            name (str): Category name

        Raises:
            CRUDException: Occurs when instantiate by the same primary keys name within same transaction
        """
        try:
            cls(name=name)
        except CacheIndexError as error:
            raise CRUDException from error

    @classmethod
    def select_all(cls) -> List[Category]:
        """Select all categories from the database.

        Returns:
            List[Category]: All categories ordered by category name
        """
        return cast(
            List[Category],
            cls.select().order_by(lambda x: x.name)[:],
        )

    @classmethod
    def select_one_by_name(cls, name: str) -> Category | None:
        """Select a category by name from the database.

        Args:
            name (str): Category name

        Returns:
            Category | None: Returns None if there is no such object.
        """
        return cast(Category | None, cls.get(name=name))


class Job(db.Entity):  # type: ignore[misc]
    _table_ = "jobs"
    id = PrimaryKey(int, auto=True)
    name = Required(str)
    category = Optional("Category")
    job_records = Set("JobRecord")
    composite_key(name, category)

    # TODO: docstring修正
    @classmethod
    def insert(cls, name: str, category: Category | None = None) -> None:
        """Insert a job to the database.
        Establish a relationship between job and category if category is given as argument.

        Raises CRUDException explicitly when trying to insert job whose category is None and that is already inserted to the database the database.
        Because most database's composite unique constraints does not work when either of them is None.

        Args:
            name (str): Job name
            category (Category | None): Category

        Raises:
            CRUDException:
                - Occurs when instantiate by the same composite keys within same transaction
                - Occurs when trying to instantiate by the same job name that is already inserted to the database if category is None
        """
        db_job: Job | None
        if category is None:
            db_job = cls.get(lambda x: x.name == name and x.category is None)
        else:
            db_job = cls.get(lambda x: x.name == name and x.category == category)
        if db_job is not None:
            raise DataAlreadyExistsError(db_job)

        try:
            cls(name=name, category=category)
        except CacheIndexError as error:
            raise CRUDException from error

    @classmethod
    def select_all(cls) -> List[Job]:
        """Select all jobs from the database.

        Returns:
            List[Job]: All jobs ordered by category name and job name
        """
        return cast(
            List[Job],
            cls.select().order_by(lambda x: (x.category.name, x.name))[:],
        )

    @classmethod
    def select_one_by_id(cls, __id: int) -> Job | None:
        """Select a job by id from the database.

        Args:
            __id (int): Job id

        Returns:
            Job | None: Returns None if there is no such object.
        """
        return cast(Job | None, cls.get(id=__id))


class JobRecord(db.Entity):  # type: ignore[misc]
    _table_ = "job_records"
    id = PrimaryKey(int, auto=True)
    job = Required("Job")
    start = Required(datetime, precision=6)
    end = Optional(datetime, precision=6)

    @classmethod
    def insert(cls, job: Job, start: DateTime, end: DateTime | None = None) -> None:
        """Insert a job record to the database.

        Args:
            job (Job): Job
            start (datetime): Start datetime
            end (datetime | None): End datetime
        """
        cls(job=job, start=start, end=end)

    @classmethod
    def update(
        cls,
        job_record: JobRecord,
        job: Job,
        start: DateTime,
        end: DateTime | None,
    ) -> None:
        """Update job record in the database

        Args:
            job_record (JobRecord): Job record
            job (Job): Job
            start (datetime): Start datetime
            end (datetime | None): End datetime
        """
        job_record.job = job
        job_record.start = start
        job_record.end = end

    @classmethod
    def update_end(cls, job_record: JobRecord, end: DateTime | None) -> None:
        """Update job record's end datetime in the database.

        Args:
            job_record (JobRecord): Job record
            end (datetime | None): End datetime
        """
        cls.update(job_record, job_record.job, job_record.start, end)

    @classmethod
    def select_all_finished_by_date(cls, __date: Date) -> List[JobRecord]:
        """Select all finished job records filtered by date from the database.

        Returns:
            List[JobRecord]: All finished job records filtered by date, and ordered by start datetime and id
        """
        return cast(
            List[JobRecord],
            cls.select(
                lambda j: j.start.date() == __date and j.end.date() == __date
            ).order_by(lambda x: (x.start, x.id))[:],
        )

    @classmethod
    def select_one_by_id(cls, __id: int) -> JobRecord | None:
        """Select a job record by id from the database.

        Args:
            __id (int): Job id

        Returns:
            JobRecord | None: Returns None if there is no such object.
        """

        return cast(JobRecord | None, cls.get(id=__id))

    @classmethod
    def select_one_in_progress_by_date(cls, __date: Date) -> JobRecord | None:
        """Select an in progress job record by date from the database.

        In progress job is equal to the end column has None.

        Args:
            __date (int): Date

        Returns:
            JobRecord | None: Returns None if there is no such object.
        """

        return cast(
            JobRecord | None,
            cls.get(lambda j: j.start.date() == __date and j.end is None),
        )

    # FIXME: comment out
    # @classmethod
    # def count_overlap_forward(cls, start: DateTime) -> int:
    #     # FIXME: 実装
    #     pass

    # @classmethod
    # def count_overlap_inward(cls, start: DateTime, end: DateTime) -> int:
    #     # FIXME: 実装
    #     pass

    # @classmethod
    # def count_overlap_backward(cls, end: DateTime) -> int:
    #     CURRENT_DATETIME: Final[datetime] = datetime.now()
    #     # fmt: off
    #     query = [
    #         "SELECT",
    #             "COUNT(*)",
    #         "FROM (",
    #             "SELECT",
    #                 f"{cls.start.column},",
    #                 "CASE",
    #                     f"WHEN {cls.end.column} is NULL THEN $CURRENT_DATETIME",
    #                     f"ELSE {cls.end.column}",
    #                     "END",
    #                     f"AS replaced_end",
    #             f"FROM {cls._table_}",
    #             "WHERE",
    #                 f"$end > {cls.start.column}",
    #                 f"AND $end <= replaced_end"
    #         ")",
    #     ]
    #     # fmt: on

    #     return db.select(" ".join(query))[0]


class Note(db.Entity):  # type: ignore[misc]
    _table_ = "notes"
    date = PrimaryKey(Date)
    content = Optional(LongStr)

    @classmethod
    def upsert(cls, __date: Date, content: str) -> None:
        """Insert note to the database if not exists.
        Update note in the database if already exists.

        Args:
            __date (date): Date
            content (str): Content
        """
        note = cast(Note | None, Note.get(date=__date))

        if note is None:
            cls(date=__date, content=content)
        else:
            note.content = content

    @classmethod
    def select_one_by_date(cls, __date: Date) -> Note | None:
        """Select a note by date from the database.

        Args:
            __date (date): Date

        Returns:
            models.JobRecord | None: None if there is no such object.
        """

        return cast(Note | None, cls.get(date=__date))
