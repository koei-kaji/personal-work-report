from typing import Final, List, Tuple, cast
from uuid import uuid4

import pytest
from pony.orm import db_session, select

from work_report import logic, view_models
from work_report.database import models

CATEGORY_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]
JOB_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]


@pytest.mark.usefixtures("fixt_init_db")
class TestRegister:
    def validate_registered_job(
        self, expected_job_name: str, expected_category_name: str | None = None
    ) -> None:
        with db_session:
            db_category: models.Category | None = None
            if expected_category_name is not None:
                db_category = models.Category.select_one_by_name(expected_category_name)

            db_job: models.Job | None
            if db_category is not None:
                db_job = models.Job.get(name=expected_job_name, category=db_category)
            else:
                db_job = models.Job.get(name=expected_job_name)

            assert type(db_job) is models.Job
            assert db_job.name == expected_job_name
            if expected_category_name is None:
                assert db_job.category is None
            else:
                assert db_job.category.name == expected_category_name
            assert db_job.job_records == set()

    def test_normal_without_category(self) -> None:
        logic.Job.register(JOB_NAMES[0])
        self.validate_registered_job(JOB_NAMES[0])

    def test_normal_with_category(self) -> None:
        logic.Category.register(CATEGORY_NAMES[0])
        logic.Job.register(JOB_NAMES[0], CATEGORY_NAMES[0])
        self.validate_registered_job(JOB_NAMES[0], CATEGORY_NAMES[0])

    def test_exc_same_name(self) -> None:
        logic.Job.register(JOB_NAMES[0])
        with pytest.raises(logic.LogicException):
            logic.Job.register(JOB_NAMES[0])

    def test_exc_same_name_and_category(self) -> None:
        logic.Category.register(CATEGORY_NAMES[0])
        logic.Job.register(JOB_NAMES[0], CATEGORY_NAMES[0])

        with pytest.raises(logic.LogicException):
            logic.Job.register(JOB_NAMES[0], CATEGORY_NAMES[0])

    def test_exc_register_not_found(self) -> None:
        with pytest.raises(logic.LogicException):
            logic.Job.register(JOB_NAMES[0], CATEGORY_NAMES[0])


@pytest.mark.usefixtures("fixt_init_db")
class TestAcquire:
    # TODO: Category=Nullの並び替えは、pythonとDBMSの実装に依存してテストしにくいので現状していない

    def register_jobs(
        self, job_names: List[str], category_names: List[str]
    ) -> List[Tuple[int, str, str]]:
        for category_name in category_names:
            logic.Category.register(category_name)
            for job_name in job_names:
                logic.Job.register(job_name, category_name)

        with db_session:
            db_job_attrs = cast(List[Tuple[int, str, str]], select((j.id, j.name, j.category.name) for j in models.Job)[:])  # type: ignore[attr-defined]

        return db_job_attrs

    def validate_all(self, expected_job_attrs: List[Tuple[int, str, str]]) -> None:
        sorted_expected_job_attrs = sorted(
            expected_job_attrs, key=lambda x: (x[2], x[1])
        )
        result = logic.Job.acquire_all()
        assert len(result) == len(sorted_expected_job_attrs)
        for i in range(len(result)):
            assert type(result[i]) is view_models.Job
            assert result[i].id == sorted_expected_job_attrs[i][0]
            assert result[i].name == sorted_expected_job_attrs[i][1]
            assert type(result[i].category) is view_models.Category
            assert result[i].category.name == sorted_expected_job_attrs[i][2]

    def test_all_normal_data_empty(self) -> None:
        self.validate_all([])

    def test_all_normal_data_exists(self) -> None:
        db_job_attrs = self.register_jobs(JOB_NAMES, CATEGORY_NAMES)
        self.validate_all(db_job_attrs)
