from typing import Final, List
from uuid import uuid4

import pytest
from pony.orm import db_session

from work_report import logic, view_models
from work_report.database import models

CATEGORY_NAME: Final[str] = str(uuid4())
CATEGORY_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]


@pytest.mark.usefixtures("fixt_init_db")
class TestRegister:
    def validate_registered_category(self, expected_category_name: str) -> None:
        with db_session:
            db_category = models.Category.select_one_by_name(expected_category_name)
            assert type(db_category) is models.Category
            assert db_category.name == expected_category_name

    def test_normal(self) -> None:
        logic.Category.register(CATEGORY_NAME)
        self.validate_registered_category(CATEGORY_NAME)

    def test_exc_same_same_pk(self) -> None:
        logic.Category.register(CATEGORY_NAME)
        with pytest.raises(logic.LogicException):
            logic.Category.register(CATEGORY_NAME)


@pytest.mark.usefixtures("fixt_init_db")
class TestAcquire:
    def register_categories(self, category_names: List[str]) -> None:
        for category_name in category_names:
            logic.Category.register(category_name)

    def validate_all(
        self,
        result_categories: List[view_models.Category],
        expected_category_names: List[str],
    ) -> None:
        sorted_expected_category_names = sorted(expected_category_names)
        assert len(result_categories) == len(sorted_expected_category_names)
        for i in range(len(result_categories)):
            assert type(result_categories[i]) is view_models.Category
            assert result_categories[i].name == sorted_expected_category_names[i]

    def test_all_normal_data_empty(self) -> None:
        result = logic.Category.acquire_all()
        self.validate_all(result, [])

    def test_all_normal_data_exists(self) -> None:
        self.register_categories(CATEGORY_NAMES)
        result = logic.Category.acquire_all()
        self.validate_all(result, CATEGORY_NAMES)
