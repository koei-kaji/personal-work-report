from datetime import date, datetime, timedelta
from typing import Final, List, Tuple
from uuid import uuid4

import pytest
from pony.orm import db_session

from work_report import logic, view_models
from work_report.database import models

CURRENT_DATE: Final[date] = datetime.now().date()
DATES: Final[List[date]] = [CURRENT_DATE + timedelta(days=i) for i in range(3)]
CONTENTS: Final[List[str]] = [str(uuid4()) for _ in range(3)]


@pytest.mark.usefixtures("fixt_init_db")
class TestSave:
    def validate_saved_note(self, __date: date, expected_content: str) -> None:
        with db_session:
            db_note = models.Note.select_one_by_date(__date)
            assert type(db_note) is models.Note
            assert db_note.date == __date
            assert db_note.content == expected_content

    def test_normal_with_empty(self) -> None:
        logic.Note.save(CURRENT_DATE, CONTENTS[0])
        self.validate_saved_note(CURRENT_DATE, CONTENTS[0])

    def test_normal_with_saved(self) -> None:
        logic.Note.save(CURRENT_DATE, CONTENTS[0])
        logic.Note.save(CURRENT_DATE, CONTENTS[1])
        self.validate_saved_note(CURRENT_DATE, CONTENTS[1])


@pytest.mark.usefixtures("fixt_init_db")
class TestAcquire:
    def register_notes(self, dates_contents: List[Tuple[date, str]]) -> None:
        for __date, content in dates_contents:
            logic.Note.save(__date, content)

    def validate_one_by_date(
        self, __date: date, expected_content: str | None, expects_none: bool = False
    ) -> None:
        db_note = logic.Note.acquire_one_by_date(__date)
        if expects_none:
            assert db_note is None
        else:
            assert type(db_note) is view_models.Note
            assert db_note.date == __date
            assert db_note.content == expected_content

    def test_one_by_date_normal_data_empty(self) -> None:
        self.validate_one_by_date(CURRENT_DATE, None, True)

    def test_one_by_date_normal_data_exists(self) -> None:
        self.register_notes(list(zip(DATES, CONTENTS)))
        self.validate_one_by_date(DATES[0], CONTENTS[0])
