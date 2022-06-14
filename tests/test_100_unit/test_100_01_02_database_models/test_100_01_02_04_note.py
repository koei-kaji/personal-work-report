from datetime import date, datetime, timedelta
from typing import Final
from uuid import uuid4

import pytest
from pony.orm import db_session

from work_report.database import models

CURRENT_DATE: Final[date] = datetime.now().date()
CONTENT: Final[str] = str(uuid4())


@pytest.mark.usefixtures("fixt_init_db")
class TestUpsert:
    def validate_registered_note(self, __date: date, expected_content: str) -> None:
        with db_session:
            db_note = models.Note.get(date=__date)
            assert type(db_note) is models.Note
            assert db_note.date == __date
            assert db_note.content == expected_content

    def test_normal_insert(self) -> None:
        with db_session:
            models.Note.upsert(CURRENT_DATE, CONTENT)

        self.validate_registered_note(CURRENT_DATE, CONTENT)

    def test_normal_upsert(self) -> None:
        with db_session:
            models.Note.upsert(CURRENT_DATE, CONTENT)

        updated_content = str(uuid4())
        with db_session:
            models.Note.upsert(CURRENT_DATE, updated_content)
        self.validate_registered_note(CURRENT_DATE, updated_content)


@pytest.mark.usefixtures("fixt_init_db")
class TestSelect:
    def register_note(self, __date: date, content: str) -> None:
        with db_session:
            models.Note.upsert(__date, content)

    def validate_one_by_date(
        self, __date: date, expected_content: str | None, expects_none: bool
    ) -> None:
        with db_session:
            db_note = models.Note.select_one_by_date(__date)
            if expects_none:
                assert db_note is None
            else:
                assert type(db_note) is models.Note
                assert db_note.date == __date
                assert db_note.content == expected_content

    def test_one_by_date_normal_data_empty(self) -> None:
        self.validate_one_by_date(CURRENT_DATE, None, True)

    def test_one_by_date_normal_data_exists(self) -> None:
        self.register_note(CURRENT_DATE, CONTENT)
        self.validate_one_by_date(CURRENT_DATE, CONTENT, False)

    def test_one_by_date_normal_data_missing(self) -> None:
        self.register_note(CURRENT_DATE, CONTENT)
        self.validate_one_by_date(CURRENT_DATE + timedelta(days=1), CONTENT, True)
