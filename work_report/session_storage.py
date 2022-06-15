from datetime import date
from enum import Enum
from typing import Any, List, cast

from pydantic import BaseModel, PrivateAttr
from streamlit.state import SessionStateProxy

from . import locale
from .view_models import Category, Job, JobRecord, Note


class KeyMessageArea(str, Enum):
    __base = "key_message_area"
    info = f"{__base}_info"
    warn = f"{__base}_warn"
    error = f"{__base}_error"
    exception = f"{__base}_exception"


class KeyDateSelection(str, Enum):
    __base = "date_selection"
    input = f"{__base}_date_input"
    button = f"{__base}_button_today"


class KeyWorkingHoursSchedule(str, Enum):
    __base = "working_hours_schedule"
    slider = f"{__base}_slider"


class KeyJobTimer(str, Enum):
    __base = "job_timer"
    selectbox = f"{__base}_selectbox"
    selectbox_disabled = f"{selectbox}_disabled"
    button_start = f"{__base}_button_start"
    button_start_disabled = f"{button_start}_disabled"
    button_stop = f"{__base}_button_stop"
    button_stop_disabled = f"{button_stop}_disabled"


class KeyTimelineChart(str, Enum):
    __base = "timeline_chart"
    chart = f"{__base}_chart"


class KeyJobAdditionManually(str, Enum):
    __base = "job_addition_manually"
    selectbox = f"{__base}_selectbox"
    selectbox_disabled = f"{selectbox}_disabled"
    slider = f"{__base}_slider"
    slider_disabled = f"{slider}_disabled"
    button = f"{__base}_button"
    button_disabled = f"{__base}_disabled"


class KeyJobCreation(str, Enum):
    __base = "job_creation"
    radio = f"{__base}_radio"
    selectbox = f"{__base}_selectbox"
    selectbox_disabled = f"{selectbox}_disabled"
    checkbox = f"{__base}_checkbox"
    checkbox_disabled = f"{checkbox}_disabled"
    input = f"{__base}_input"
    button = f"{__base}_button"
    button_disabled = f"{button}_disabled"


class KeyJobLogs(str, Enum):
    __base = "job_logs"
    selectbox = f"{__base}_selectbox"
    slider = f"{__base}_slider"
    button = f"{__base}_button"


class KeyNoteArea(str, Enum):
    __base = "note_area"
    text_area = f"{__base}_text_area"
    button = f"{__base}_button"


class KeyLanguageSelection(str, Enum):
    __base = "language_selection"
    selectbox = f"{__base}_selectbox"


class RadioJobCreation(str, Enum):
    job = "job"
    category = "category"

    @classmethod
    def get_values(cls) -> List[str]:
        return [e.value for e in cls]


class SessionStorage(BaseModel):
    state: SessionStateProxy
    key_message_area: KeyMessageArea = KeyMessageArea  # type: ignore[assignment]
    key_date_selection: KeyDateSelection = KeyDateSelection  # type: ignore[assignment]
    key_working_hours_schedule: KeyWorkingHoursSchedule = KeyWorkingHoursSchedule  # type: ignore[assignment]
    key_job_timer: KeyJobTimer = KeyJobTimer  # type: ignore[assignment]
    key_timeline_chart: KeyTimelineChart = KeyTimelineChart  # type: ignore[assignment]
    key_job_addition_manually: KeyJobAdditionManually = KeyJobAdditionManually  # type: ignore[assignment]
    key_job_creation: KeyJobCreation = KeyJobCreation  # type: ignore[assignment]
    key_job_logs: KeyJobLogs = KeyJobLogs  # type: ignore[assignment]
    key_note_area: KeyNoteArea = KeyNoteArea  # type: ignore[assignment]
    key_language_selection: KeyLanguageSelection = KeyLanguageSelection  # type: ignore[assignment]

    job_creation_radio_values: List[str] = RadioJobCreation.get_values()

    # NOTE: mediatorによって設定される
    __jobs: List[Job] = PrivateAttr()
    __job_records: List[JobRecord] = PrivateAttr()
    __job_record_in_progress: JobRecord | None = PrivateAttr()
    __categories: List[Category] = PrivateAttr()
    __note: Note | None = PrivateAttr()
    __language: locale.Language = PrivateAttr()

    def init_state(self, key: str, value: Any) -> None:
        if key not in self.state:
            self.state[key] = value

    def set_state(self, key: str, value: Any, *, do_init: bool = False) -> None:
        if do_init:
            self.init_state(key, value)

        self.state[key] = value

    def get_state(self, key: str) -> Any:
        return self.state.get(key, None)

    def get_selected_date(self) -> date:
        return cast(date, self.get_state(self.key_date_selection.input))

    def set_jobs(self, jobs: List[Job]) -> None:
        self.__jobs = jobs

    def get_jobs(self) -> List[Job]:
        return self.__jobs

    def set_job_records(self, job_records: List[JobRecord]) -> None:
        self.__job_records = job_records

    def get_job_records(self) -> List[JobRecord]:
        return self.__job_records

    def set_job_record_in_progress(self, job_record: JobRecord | None) -> None:
        self.__job_record_in_progress = job_record

    def get_job_record_in_progress(self) -> JobRecord | None:
        return self.__job_record_in_progress

    def set_categories(self, categories: List[Category]) -> None:
        self.__categories = categories

    def get_categories(self) -> List[Category]:
        return self.__categories

    def set_note(self, note: Note | None) -> None:
        self.__note = note

    def get_note(self) -> Note | None:
        return self.__note

    def set_language(self, language: locale.Language) -> None:
        self.__language = language

    def get_language(self) -> locale.Language:
        return self.__language

    def get_languages(self) -> List[locale.Language]:
        return [locale.LanguageEN(), locale.LanguageJP()]

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True
        copy_on_model_validation = False
