from typing import Final, List
from uuid import uuid4

import pytest
from pony.orm import db_session
from pony.orm.core import TransactionIntegrityError

from work_report.database import models

CATEGORY_NAME: Final[str] = str(uuid4())
CATEGORY_NAMES: Final[List[str]] = [str(uuid4()) for _ in range(3)]


class TestInsert:
    def test_normal(self, fixt_init_db: None) -> None:
        with db_session:
            models.Category.insert(CATEGORY_NAME)

        with db_session:
            db_category = models.Category.get(name=CATEGORY_NAME)
            assert type(db_category) is models.Category
            assert db_category.name == CATEGORY_NAME
            assert db_category.jobs == set()

    def test_exc_same_pk_inside_txn(self, fixt_init_db: None) -> None:
        with db_session:
            with pytest.raises(models.CRUDException):
                models.Category.insert(CATEGORY_NAME)
                models.Category.insert(CATEGORY_NAME)

    def test_exc_same_pk_separate_txn(self, fixt_init_db: None) -> None:
        # OK
        with db_session:
            models.Category.insert(CATEGORY_NAME)

        # Error: CRUDException isn't raised because an error occurs at the db_session.
        with pytest.raises(TransactionIntegrityError):
            with db_session:
                models.Category.insert(CATEGORY_NAME)


class TestSelect:
    def register_categories(self, category_names: List[str]) -> None:
        with db_session:
            for category_name in category_names:
                models.Category.insert(category_name)

    def validate_all(self, expected_names: List[str]) -> None:
        sorted_expected_names = sorted(expected_names)
        with db_session:
            db_categories = models.Category.select_all()
            assert len(db_categories) == len(sorted_expected_names)
            for i in range(len(db_categories)):
                assert db_categories[i].name == sorted_expected_names[i]

    def validate_one_by_name(
        self, name: str, expected_category_name: str | None
    ) -> None:
        with db_session:
            db_category = models.Category.select_one_by_name(name)
            if expected_category_name is None:
                assert db_category is None
            else:
                assert type(db_category) is models.Category
                assert db_category.name == expected_category_name

    def test_all_normal_data_empty(self, fixt_init_db: None) -> None:
        self.validate_all([])

    def test_all_normal_data_exists(self, fixt_init_db: None) -> None:
        self.register_categories(CATEGORY_NAMES)
        self.validate_all(CATEGORY_NAMES)

    def test_one_by_name_normal_data_empty(self, fixt_init_db: None) -> None:
        self.validate_one_by_name("nothing", None)

    def test_one_by_name_normal_data_exists(self, fixt_init_db: None) -> None:
        self.register_categories(CATEGORY_NAMES)
        for category_name in CATEGORY_NAMES:
            self.validate_one_by_name(category_name, category_name)

    def test_one_by_name_normal_data_missing(self, fixt_init_db: None) -> None:
        self.validate_one_by_name(str(uuid4()), None)
