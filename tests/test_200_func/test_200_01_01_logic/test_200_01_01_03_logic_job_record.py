from datetime import date, datetime, timedelta
from typing import Final, List, Tuple, cast
from uuid import uuid4

import pytest
from pony.orm import db_session, select

from work_report import logic, view_models
from work_report.database import models

CATEGORY_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]
JOB_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]
CURRENT_DATE: Final[date] = datetime.now().date()
START_DATETIMES: Final[List[datetime]] = [
    datetime.combine(CURRENT_DATE, datetime.now().time())
    + timedelta(hours=-(i + 1), minutes=(i + 1))
    for i in range(3)
]
END_DATETIMES: Final[List[datetime]] = [
    START_DATETIMES[i] + timedelta(minutes=1) for i in range(3)
]


def register_jobs(
    job_names: List[str], category_names: List[str]
) -> List[Tuple[int, str, str]]:
    for category_name in category_names:
        logic.Category.register(category_name)
        for job_name in job_names:
            logic.Job.register(job_name, category_name)

    with db_session:
        db_job_attrs = cast(List[Tuple[int, str, str]], select((j.id, j.name, j.category.name) for j in models.Job)[:])  # type: ignore[attr-defined]

    return db_job_attrs


@pytest.mark.usefixtures("fixt_init_db")
class TestRegister:
    def validate_registered_job_record(
        self, expected_job_id: int, expected_start: datetime, expected_end: datetime
    ) -> None:
        replaced_second_expected_start = expected_start.replace(second=0, microsecond=0)
        repalced_second_expected_end = expected_end.replace(second=0, microsecond=0)
        with db_session:
            db_job_record = models.JobRecord.get(
                lambda x: x.job.id == expected_job_id
                and x.start == replaced_second_expected_start
                and x.end == repalced_second_expected_end
            )
            assert type(db_job_record) is models.JobRecord
            assert type(db_job_record.id) is int
            assert db_job_record.job.id == expected_job_id
            assert db_job_record.start == replaced_second_expected_start
            assert db_job_record.end == repalced_second_expected_end

    def test_normal(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        logic.JobRecord.register(
            db_job_attrs[0][0], START_DATETIMES[0], END_DATETIMES[0]
        )
        self.validate_registered_job_record(
            db_job_attrs[0][0], START_DATETIMES[0], END_DATETIMES[0]
        )

    def test_exc_job_not_found(self) -> None:
        with pytest.raises(logic.LogicException):
            logic.JobRecord.register(999, START_DATETIMES[0], END_DATETIMES[0])

    def test_exc_end_equals_to_start(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        with pytest.raises(logic.LogicException):
            logic.JobRecord.register(
                db_job_attrs[0][0], START_DATETIMES[0], START_DATETIMES[0]
            )

    def test_exc_end_less_than_start(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        with pytest.raises(logic.LogicException):
            logic.JobRecord.register(
                db_job_attrs[0][0], END_DATETIMES[0], START_DATETIMES[0]
            )

    def test_exc_diff_dates(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        with pytest.raises(logic.LogicException):
            logic.JobRecord.register(
                db_job_attrs[0][0],
                START_DATETIMES[0],
                END_DATETIMES[0] + timedelta(days=1),
            )


@pytest.mark.usefixtures("fixt_init_db")
class TestRevise:
    def register_job_record(
        self, job_id: int, start: datetime, end: datetime
    ) -> Tuple[int, int, datetime, datetime]:
        logic.JobRecord.register(job_id, start, end)
        with db_session:
            db_job_record_attr = cast(
                Tuple[int, int, datetime, datetime],
                select(
                    (jr.id, jr.job.id, jr.start, jr.end) for jr in models.JobRecord  # type: ignore[attr-defined]
                ).get(),
            )

        return db_job_record_attr

    def validate_revised_job_record(
        self,
        job_record_id: int,
        expected_job_id: int,
        expected_start: datetime,
        expected_end: datetime,
    ) -> None:
        replaced_second_expected_start = expected_start.replace(second=0, microsecond=0)
        repalced_second_expected_end = expected_end.replace(second=0, microsecond=0)
        with db_session:
            db_job_record = models.JobRecord.select_one_by_id(job_record_id)
            assert type(db_job_record) is models.JobRecord
            assert db_job_record.id == job_record_id
            assert type(db_job_record.job) is models.Job
            assert db_job_record.job.id == expected_job_id
            assert db_job_record.start == replaced_second_expected_start
            assert db_job_record.end == repalced_second_expected_end

    def test_normal(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_attr = self.register_job_record(
            db_job_attrs[0][0], START_DATETIMES[0], END_DATETIMES[0]
        )
        logic.JobRecord.revise(
            db_job_record_attr[0],
            db_job_attrs[1][0],
            START_DATETIMES[1],
            END_DATETIMES[1],
        )
        self.validate_revised_job_record(
            db_job_record_attr[0],
            db_job_attrs[1][0],
            START_DATETIMES[1],
            END_DATETIMES[1],
        )

    def test_exc_job_not_found(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        with pytest.raises(logic.LogicException):
            logic.JobRecord.revise(
                999, db_job_attrs[0], START_DATETIMES[0], END_DATETIMES[0]
            )

    def test_exc_end_equals_to_start(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_attr = self.register_job_record(
            db_job_attrs[0][0], START_DATETIMES[0], END_DATETIMES[0]
        )
        with pytest.raises(logic.LogicException):
            logic.JobRecord.revise(
                db_job_record_attr[0],
                db_job_attrs[1][0],
                START_DATETIMES[1],
                START_DATETIMES[1],
            )

    def test_exc_end_less_than_start(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_attr = self.register_job_record(
            db_job_attrs[0][0], START_DATETIMES[0], END_DATETIMES[0]
        )
        with pytest.raises(logic.LogicException):
            logic.JobRecord.revise(
                db_job_record_attr[0],
                db_job_attrs[1][0],
                END_DATETIMES[1],
                START_DATETIMES[1],
            )

    def test_exc_diff_dates(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_attr = self.register_job_record(
            db_job_attrs[0][0], START_DATETIMES[0], END_DATETIMES[0]
        )
        with pytest.raises(logic.LogicException):
            logic.JobRecord.revise(
                db_job_record_attr[0],
                db_job_attrs[1][0],
                START_DATETIMES[1],
                END_DATETIMES[1] + timedelta(days=1),
            )


@pytest.mark.usefixtures("fixt_init_db")
class TestStart:
    def validate_started_job_record(
        self,
        expected_db_job_id: int,
        before_datetime: datetime,
        after_datetime: datetime,
    ) -> None:
        replaced_before_datetime = before_datetime.replace(second=0, microsecond=0)
        replaced_after_datetime = after_datetime.replace(second=0, microsecond=0)
        with db_session:
            db_job_record = models.JobRecord.select_one_in_progress_by_date(
                before_datetime.date()
            )
            assert type(db_job_record) is models.JobRecord
            assert type(db_job_record.job) is models.Job
            assert db_job_record.job.id == expected_db_job_id
            assert (
                replaced_before_datetime
                <= db_job_record.start
                <= replaced_after_datetime
            )
            assert db_job_record.end is None

    def test_normal(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        before_datetime = datetime.combine(CURRENT_DATE, datetime.now().time())
        logic.JobRecord.start(db_job_attrs[0][0])
        after_datetime = datetime.combine(CURRENT_DATE, datetime.now().time())
        self.validate_started_job_record(
            db_job_attrs[0][0], before_datetime, after_datetime
        )

    def test_exc_job_not_found(self) -> None:
        with pytest.raises(logic.LogicException):
            logic.JobRecord.start(999)

    def test_exc_job_already_started(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        logic.JobRecord.start(db_job_attrs[0][0])

        with pytest.raises(logic.LogicException):
            logic.JobRecord.start(db_job_attrs[1][0])


@pytest.mark.usefixtures("fixt_init_db")
class TestStop:
    def validate_stopped_job_record(
        self,
        job_record_id: int,
        expected_db_job_id: int,
        expected_start: datetime,
        before_datetime_stop: datetime,
        after_datetime_stop: datetime,
    ) -> None:
        replaced_before_datetime = before_datetime_stop.replace(second=0, microsecond=0)
        replaced_after_datetime = after_datetime_stop.replace(second=0, microsecond=0)
        with db_session:
            db_job_record = models.JobRecord.select_one_by_id(job_record_id)
            assert type(db_job_record) is models.JobRecord
            assert db_job_record.id == job_record_id
            assert type(db_job_record.job) is models.Job
            assert db_job_record.job.id == expected_db_job_id
            assert db_job_record.start == expected_start
            assert (
                replaced_before_datetime
                <= db_job_record.start
                <= replaced_after_datetime
            )

    def start_job(self, job_id: int) -> Tuple[int, datetime]:
        logic.JobRecord.start(job_id)

        db_job_record_id: int
        db_job_record_start: datetime
        with db_session:
            db_job_record = models.JobRecord.select_one_in_progress_by_date(
                CURRENT_DATE
            )
            if db_job_record is None:
                raise Exception("!?!?!?")
            db_job_record_id = db_job_record.id
            db_job_record_start = db_job_record.start

        return db_job_record_id, db_job_record_start

    def test_normal(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_id, db_job_record_start = self.start_job(db_job_attrs[0][0])
        before_datetime = datetime.combine(CURRENT_DATE, datetime.now().time())
        logic.JobRecord.stop(db_job_record_id)
        after_datetime = datetime.combine(CURRENT_DATE, datetime.now().time())
        self.validate_stopped_job_record(
            db_job_record_id,
            db_job_attrs[0][0],
            db_job_record_start,
            before_datetime,
            after_datetime,
        )

    def test_exc_job_not_found(self) -> None:
        with pytest.raises(logic.LogicException):
            logic.JobRecord.stop(999)

    def test_exc_job_already_stopped(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_id, _ = self.start_job(db_job_attrs[0][0])
        logic.JobRecord.stop(db_job_record_id)

        with pytest.raises(logic.LogicException):
            logic.JobRecord.stop(db_job_record_id)


@pytest.mark.usefixtures("fixt_init_db")
class TestAcquire:
    def register_job_records(
        self,
        job_id: int,
        starts_ends: List[Tuple[datetime, datetime]],
        is_last_working: bool = False,
    ) -> List[Tuple[int, int, datetime, datetime | None]]:
        for start, end in starts_ends[:-1]:
            logic.JobRecord.register(job_id, start, end)
        if is_last_working:
            with db_session:
                db_job = models.Job.select_one_by_id(job_id)
                if db_job is None:
                    raise Exception("!?!?!?")
                models.JobRecord.insert(db_job, starts_ends[-1][0])
        else:
            logic.JobRecord.register(job_id, starts_ends[-1][0], starts_ends[-1][1])

        with db_session:
            db_job_record_attrs = cast(
                List[Tuple[int, int, datetime, datetime | None]],
                select(
                    (jr.id, jr.job.id, jr.start, jr.end) for jr in models.JobRecord  # type: ignore[attr-defined]
                )[:],
            )

        return db_job_record_attrs

    def validate_all_by_date(
        self,
        __date: date,
        expected_job_record_attrs: List[Tuple[int, int, datetime, datetime | None]],
    ) -> None:
        sorted_expected_job_record_attrs = sorted(
            expected_job_record_attrs, key=lambda x: (x[2], x[0])
        )
        result = logic.JobRecord.acquire_all_finished_by_date(__date)

        assert len(result) == len(sorted_expected_job_record_attrs)
        for i in range(len(result)):
            assert type(result[i]) is view_models.JobRecord
            assert result[i].id == sorted_expected_job_record_attrs[i][0]
            assert type(result[i].job) is view_models.Job
            assert result[i].job.id == sorted_expected_job_record_attrs[i][1]
            assert result[i].start == sorted_expected_job_record_attrs[i][2]
            assert result[i].end == sorted_expected_job_record_attrs[i][3]

    def validate_one_in_progress_by_date(
        self,
        __date: date,
        expected_job_record_id: int | None,
        expected_job_id: int | None,
        expected_start: datetime | None,
        expects_none: bool = False,
    ) -> None:
        result = logic.JobRecord.acquire_one_in_progress_by_date(__date)
        if expects_none:
            assert result is None
        else:
            assert type(result) is view_models.JobRecord
            assert result.id == expected_job_record_id
            assert type(result.job) is view_models.Job
            assert result.job.id == expected_job_id
            assert result.start == expected_start
            assert result.end is None

    def test_all_by_date_normal_data_empty(self) -> None:
        self.validate_all_by_date(CURRENT_DATE, [])

    def test_all_by_date_normal_data_exists(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_attrs = self.register_job_records(
            db_job_attrs[0][0], list(zip(START_DATETIMES, END_DATETIMES))
        )
        self.validate_all_by_date(CURRENT_DATE, db_job_record_attrs)

    def test_all_by_date_normal_data_include_in_progress(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_attrs = self.register_job_records(
            db_job_attrs[0][0], list(zip(START_DATETIMES, END_DATETIMES)), True
        )
        db_job_record_attrs = [
            attr for attr in db_job_record_attrs if attr[3] is not None
        ]
        self.validate_all_by_date(CURRENT_DATE, db_job_record_attrs)

    def test_one_in_progress_by_date_normal_data_empty(self) -> None:
        self.validate_one_in_progress_by_date(CURRENT_DATE, None, None, None, True)

    def test_one_in_progress_by_date_normal_data_exists(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        db_job_record_attrs = self.register_job_records(
            db_job_attrs[0][0], list(zip(START_DATETIMES, END_DATETIMES)), True
        )
        db_job_record_attr = [
            attr for attr in db_job_record_attrs if attr[3] is None
        ].pop()
        self.validate_one_in_progress_by_date(
            CURRENT_DATE,
            db_job_record_attr[0],
            db_job_record_attr[1],
            db_job_record_attr[2],
        )

    def test_one_in_progress_by_date_normal_data_not_found(self) -> None:
        db_job_attrs = register_jobs(JOB_NAMES, CATEGORY_NAMES)
        self.register_job_records(
            db_job_attrs[0][0], list(zip(START_DATETIMES, END_DATETIMES))
        )
        self.validate_one_in_progress_by_date(CURRENT_DATE, None, None, None, True)
