import random
from datetime import date, datetime, timedelta
from typing import Final, List, Tuple, cast
from uuid import uuid4

import pytest
from pony.orm import db_session, select

from work_report.database import models

JOB_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]
CURRENT_DATE: Final[date] = datetime.now().date()
START: Final[datetime] = datetime.now()
END: Final[datetime] = datetime.now()


@pytest.mark.usefixtures("fixt_init_db")
class TestInsert:
    def register_jobs(self, job_names: List[str]) -> List[int]:
        with db_session:
            for job_name in job_names:
                models.Job.insert(job_name)

            db_job_ids = cast(List[int], select(j.id for j in models.Job)[:])  # type: ignore[attr-defined]

        return db_job_ids

    def validate_registered_job_record(
        self,
        expected_job_id: int,
        expected_start: datetime,
        expected_end: datetime | None,
    ) -> None:
        with db_session:
            db_job_record: models.JobRecord
            if expected_end is None:
                db_job_record = models.JobRecord.get(
                    lambda x: x.job.id == expected_job_id
                    and x.start == expected_start
                    and x.end == None
                )
            else:
                db_job_record = models.JobRecord.get(
                    lambda x: x.job.id == expected_job_id
                    and x.start == expected_start
                    and x.end == expected_end
                )
            assert type(db_job_record) is models.JobRecord
            assert type(db_job_record.job) is models.Job
            assert db_job_record.job.id == expected_job_id
            assert db_job_record.start == expected_start
            assert db_job_record.end == expected_end

    @pytest.mark.parametrize(("end"), [(datetime.now()), (None)])
    def test_normal(self, end: datetime | None) -> None:
        db_job_ids = self.register_jobs(JOB_NAMES)

        job_record_attrs: List[
            Tuple[int, datetime, datetime | None]
        ] = []  # job_id, start, end
        with db_session:
            for db_job_id in db_job_ids:
                db_job = models.Job.select_one_by_id(db_job_id)
                if db_job is None:
                    raise Exception("!?!?!?")
                start = datetime.now()

                models.JobRecord.insert(db_job, start, end)
                job_record_attrs.append((db_job_id, start, end))

        for job_record_attr in job_record_attrs:
            self.validate_registered_job_record(*job_record_attr)


@pytest.mark.usefixtures("fixt_init_db")
class TestUpdate:
    def register_job_records(self, job_names: List[str]) -> Tuple[List[int], List[int]]:
        with db_session:
            for job_name in job_names:
                models.Job.insert(job_name)

            db_jobs = models.Job.select()[:]
            for db_job in db_jobs:
                models.JobRecord.insert(db_job, datetime.now(), None)

            db_job_ids = select(j.id for j in models.Job)[:]  # type: ignore[attr-defined]
            db_job_record_ids = select(jr.id for jr in models.JobRecord)[:]  # type: ignore[attr-defined]

        return db_job_ids, db_job_record_ids

    @pytest.mark.parametrize(("replaced_end"), [(datetime.now()), (None)])
    def test_normal(self, replaced_end: datetime | None) -> None:
        db_job_ids, db_job_record_ids = self.register_job_records(JOB_NAMES)
        with db_session:
            for db_job_record_id in db_job_record_ids:
                db_job_id = random.choice(db_job_ids)

                db_job = models.Job.select_one_by_id(db_job_id)
                db_job_record = cast(
                    models.JobRecord | None, models.JobRecord.get(id=db_job_record_id)
                )
                if db_job is None:
                    raise Exception()
                if db_job_record is None:
                    raise Exception()

                replaced_start = datetime.now()
                models.JobRecord.update(
                    db_job_record, db_job, replaced_start, replaced_end
                )

                assert db_job_record.job.id == db_job_id
                assert db_job_record.start == replaced_start
                assert db_job_record.end == replaced_end

    @pytest.mark.parametrize(("replaced_end"), [(datetime.now()), (None)])
    def test_end_normal(self, replaced_end: datetime | None) -> None:
        _, db_job_record_ids = self.register_job_records(JOB_NAMES)
        with db_session:
            for db_job_record_id in db_job_record_ids:
                db_job_record = models.JobRecord.get(id=db_job_record_id)

                job_id = db_job_record.job.id
                start = db_job_record.start

                models.JobRecord.update_end(db_job_record, replaced_end)

                assert db_job_record.job.id == job_id
                assert db_job_record.start == start
                assert db_job_record.end == replaced_end


@pytest.mark.usefixtures("fixt_init_db")
class TestSelect:
    def register_job_records(
        self, job_names: List[str], __date: date, is_finished: bool
    ) -> List[Tuple[int, int, datetime, datetime | None]]:
        with db_session:
            for job_name in job_names:
                models.Job.insert(job_name)

            db_jobs = models.Job.select()[:]
            for db_job in db_jobs:
                start = datetime.combine(__date, datetime.now().time())
                end = start + timedelta(minutes=1) if is_finished else None
                models.JobRecord.insert(db_job, start, end)

            db_job_record_attrs = cast(
                List[Tuple[int, int, datetime, datetime | None]],
                select(
                    (jr.id, jr.job.id, jr.start, jr.end) for jr in models.JobRecord  # type: ignore[attr-defined]
                )[:],
            )

        return db_job_record_attrs

    def register_job_record(
        self, job_name: str, __date: date, is_finished: bool
    ) -> Tuple[int, int, datetime, datetime | None]:
        with db_session:
            models.Job.insert(job_name)

            db_job = models.Job.get()
            # start = datetime.combine(__date, datetime.now().time()) + timedelta(
            #     minutes=random.randint(1, 59)
            # )
            start = datetime.combine(__date, datetime.now().time())
            end = start + timedelta(minutes=1) if is_finished else None
            models.JobRecord.insert(db_job, start, end)

            db_job_record_attr = cast(
                Tuple[int, int, datetime, datetime | None],
                select(
                    (jr.id, jr.job.id, jr.start, jr.end) for jr in models.JobRecord  # type: ignore[attr-defined]
                ).get(),
            )

        return db_job_record_attr

    def validate_all_finished_by_date(
        self,
        __date: date,
        expected_job_record_attrs: List[Tuple[int, int, datetime, datetime | None]],
    ) -> None:
        sorted_expected_job_record_attrs = sorted(
            expected_job_record_attrs, key=lambda x: (x[2], x[0])
        )
        with db_session:
            db_job_records = models.JobRecord.select_all_finished_by_date(__date)

            assert len(db_job_records) == len(sorted_expected_job_record_attrs)
            for i in range(len(db_job_records)):
                assert db_job_records[i].id == sorted_expected_job_record_attrs[i][0]
                assert (
                    db_job_records[i].job.id == sorted_expected_job_record_attrs[i][1]
                )
                assert db_job_records[i].start == sorted_expected_job_record_attrs[i][2]
                if sorted_expected_job_record_attrs[i][3] is None:
                    assert db_job_records[i].end is None
                else:
                    assert (
                        db_job_records[i].end == sorted_expected_job_record_attrs[i][3]
                    )

    def validate_one_session_inner(
        self,
        job_record: models.JobRecord | None,
        expected_job_id: int | None,
        expected_start: datetime | None,
        expected_end: datetime | None,
        expects_none: bool = False,
    ) -> None:
        if expects_none:
            assert job_record is None
        else:
            assert type(job_record) is models.JobRecord
            assert job_record.job.id == expected_job_id
            assert job_record.start == expected_start
            assert job_record.end == expected_end

    def validate_one_by_id(
        self,
        job_record_id: int,
        expected_job_id: int | None,
        expected_start: datetime | None,
        expected_end: datetime | None,
        expects_none: bool = False,
    ) -> None:
        with db_session:
            db_job_record = models.JobRecord.select_one_by_id(job_record_id)
            self.validate_one_session_inner(
                db_job_record,
                expected_job_id,
                expected_start,
                expected_end,
                expects_none,
            )

    def validate_one_in_progress_by_date(
        self,
        __date: date,
        expected_job_id: int | None,
        expected_start: datetime | None,
        expected_end: datetime | None,
        expects_none: bool = False,
    ) -> None:
        with db_session:
            db_job_record = models.JobRecord.select_one_in_progress_by_date(__date)
            self.validate_one_session_inner(
                db_job_record,
                expected_job_id,
                expected_start,
                expected_end,
                expects_none,
            )

    def test_all_finished_by_date_normal_date_empty(self) -> None:
        self.validate_all_finished_by_date(CURRENT_DATE, [])

    def test_all_finished_by_date_normal_data_exists(self) -> None:
        db_job_record_attrs = self.register_job_records(JOB_NAMES, CURRENT_DATE, True)
        self.validate_all_finished_by_date(CURRENT_DATE, db_job_record_attrs)

    def test_all_finished_by_date_data_missing_for_in_progress(self) -> None:
        self.register_job_records(JOB_NAMES, CURRENT_DATE, False)
        self.validate_all_finished_by_date(CURRENT_DATE, [])

    def test_all_finished_by_date_data_missing_for_wrong_dates(self) -> None:
        self.register_job_records(JOB_NAMES, CURRENT_DATE + timedelta(days=1), True)
        self.validate_all_finished_by_date(CURRENT_DATE, [])

    def test_one_by_id_normal_data_empty(self) -> None:
        self.validate_one_by_id(999, None, None, None, True)

    def test_one_by_id_normal_data_exists(self) -> None:
        db_job_record_attrs = self.register_job_records(JOB_NAMES, CURRENT_DATE, True)
        for db_job_record_attr in db_job_record_attrs:
            self.validate_one_by_id(*db_job_record_attr)

    def test_one_by_id_normal_data_missing(self) -> None:
        self.register_job_records(JOB_NAMES, CURRENT_DATE, True)
        self.validate_one_by_id(999, None, None, None, True)

    def test_one_in_progress_by_date_normal_data_empty(self) -> None:
        self.validate_one_in_progress_by_date(CURRENT_DATE, None, None, None, True)

    def test_one_in_progress_by_date_normal_data_exists(self) -> None:
        db_job_record_attr = self.register_job_record(
            random.choice(JOB_NAMES), CURRENT_DATE, False
        )
        self.validate_one_in_progress_by_date(CURRENT_DATE, *db_job_record_attr[1:])

    def test_one_in_progress_by_date_normal_data_missing(self) -> None:
        self.register_job_record(random.choice(JOB_NAMES), CURRENT_DATE, False)
        self.validate_one_in_progress_by_date(
            CURRENT_DATE + timedelta(days=1), None, None, None, True
        )


@pytest.mark.usefixtures("fixt_init_db")
class TestCountOverlap:
    # FIXME: 実装
    # def test_count_overlap_backward_normal_exists(self, get_test_db: DB) -> None:
    #     CURRENT_DATETIME: Final[datetime] = datetime.now() - timedelta(minutes=1)
    #     with db_session:
    #         job = models.Job(name="test")
    #         models.JobRecord(job=job, start=CURRENT_DATETIME - timedelta(minutes=1))

    #         result = models.JobRecord.count_overlap_backward(CURRENT_DATETIME)

    #         assert result == 1
    pass
