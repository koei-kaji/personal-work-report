import itertools
from typing import Final, List
from uuid import uuid4

import pytest
from pony.orm import db_session, select

from work_report.database import models

CATEGORY_NAME: Final[str] = str(uuid4())
CATEGORY_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]
JOB_NAME: Final[str] = str(uuid4())
JOB_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]


@pytest.mark.usefixtures("fixt_init_db")
class TestInsert:
    def validate_registered_job(
        self, expected_job_name: str, expected_category_name: str | None
    ) -> None:
        with db_session:
            db_job: models.Job
            if expected_category_name is None:
                db_job = models.Job.get(
                    lambda x: x.name == expected_job_name and x.category is None
                )
            else:
                db_job = models.Job.get(
                    lambda x: x.name == expected_job_name
                    and x.category.name == expected_category_name
                )

            assert type(db_job) is models.Job
            assert type(db_job.id) is int
            assert db_job.name == expected_job_name
            if expected_category_name is None:
                assert db_job.category is None
            else:
                assert type(db_job.category) is models.Category
                assert db_job.category.name == expected_category_name
                assert len(db_job.category.jobs) == 1

    def test_normal_without_category(self) -> None:
        with db_session:
            models.Job.insert(JOB_NAME)

        self.validate_registered_job(JOB_NAME, None)

    def test_normal_with_category(self) -> None:
        # カテゴリー登録
        with db_session:
            models.Category.insert(CATEGORY_NAME)

        with db_session:
            db_category = models.Category.get(name=CATEGORY_NAME)
            models.Job.insert(JOB_NAME, db_category)

        self.validate_registered_job(JOB_NAME, CATEGORY_NAME)

    def test_exc_same_job_inside_txn(self) -> None:
        with db_session:
            with pytest.raises(models.DataAlreadyExistsError):
                models.Job.insert(JOB_NAME)
                models.Job.insert(JOB_NAME)

    def test_exc_same_job_separate_txn(self) -> None:
        with db_session:
            models.Job.insert(JOB_NAME)

        with db_session:
            with pytest.raises(models.DataAlreadyExistsError):
                models.Job.insert(JOB_NAME)

    def test_exc_same_job_and_category_inside_txn(self) -> None:
        # カテゴリー登録
        with db_session:
            models.Category.insert(CATEGORY_NAME)

        with db_session:
            db_category = models.Category.get(name=CATEGORY_NAME)
            with pytest.raises(models.DataAlreadyExistsError):
                models.Job.insert(JOB_NAME, db_category)
                models.Job.insert(JOB_NAME, db_category)

    def test_exc_same_job_and_category_separate_txn(self) -> None:
        # カテゴリー登録
        with db_session:
            models.Category.insert(CATEGORY_NAME)

        with db_session:
            db_category = models.Category.get(name=CATEGORY_NAME)
            models.Job.insert(JOB_NAME, db_category)

        with db_session:
            db_category = models.Category.get(name=CATEGORY_NAME)
            with pytest.raises(models.DataAlreadyExistsError):
                models.Job.insert(JOB_NAME, db_category)


@pytest.mark.usefixtures("fixt_init_db")
class TestSelect:
    def register_categories_jobs(
        self,
        category_names: List[str],
        job_names: List[str],
        *,
        registers_category_none: bool = False
    ) -> None:
        with db_session:
            for category_name in category_names:
                models.Category.insert(category_name)
                db_category = models.Category.select_one_by_name(category_name)
                for job_name in job_names:
                    models.Job.insert(job_name, db_category)

            if registers_category_none:
                for job_name in job_names:
                    models.Job.insert(job_name)

    def validate_all(
        self, expected_category_names: List[str], expected_job_names: List[str]
    ) -> None:
        sorted_combinations = sorted(
            list(itertools.product(expected_category_names, expected_job_names)),
            key=lambda x: (x[0], x[1]),
        )

        with db_session:
            db_jobs = models.Job.select_all()

            assert len(db_jobs) == len(sorted_combinations)
            for i in range(len(db_jobs)):
                assert db_jobs[i].category.name == sorted_combinations[i][0]
                assert db_jobs[i].name == sorted_combinations[i][1]

    def validate_one(
        self,
        expected_category_name: str | None,
        expected_job_name: str | None,
        *,
        job_id: int | None = None
    ) -> None:
        with db_session:
            if job_id is None:
                if expected_category_name is None:
                    job_id = select(
                        j.id
                        for j in models.Job  # type: ignore[attr-defined]
                        if j.name == expected_job_name and j.category is None
                    ).get()
                else:
                    job_id = select(
                        j.id
                        for j in models.Job  # type: ignore[attr-defined]
                        if j.name == expected_job_name
                        and j.category.name == expected_category_name
                    ).get()
            db_job = models.Job.select_one_by_id(job_id)
            if expected_job_name is None:
                assert db_job is None
            else:
                assert type(db_job) is models.Job
                assert db_job.id == job_id
                assert db_job.name == expected_job_name
                if expected_category_name is None:
                    assert db_job.category is None
                else:
                    assert db_job.category.name == expected_category_name

    def test_all_normal_data_empty(self) -> None:
        self.validate_all([], [])

    def test_all_normal_data_exists(self) -> None:
        self.register_categories_jobs(CATEGORY_NAMES, JOB_NAMES)
        self.validate_all(CATEGORY_NAMES, JOB_NAMES)

    def test_one_by_id_normal_data_empty(self) -> None:
        self.validate_one(None, None, job_id=999)

    def test_one_by_id_normal_data_exists(self) -> None:
        self.register_categories_jobs(
            CATEGORY_NAMES, JOB_NAMES, registers_category_none=True
        )
        for job_name in JOB_NAMES:
            for category_name in CATEGORY_NAMES:
                self.validate_one(category_name, job_name)
            self.validate_one(None, job_name)

    def test_one_by_id_normal_data_missing(self) -> None:
        self.register_categories_jobs(
            CATEGORY_NAMES, JOB_NAMES, registers_category_none=True
        )
        self.validate_one(None, None, job_id=999)
