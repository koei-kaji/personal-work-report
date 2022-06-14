from datetime import date, datetime
from typing import Any

from pydantic import BaseModel

from . import logic, session_storage
from .config import DatabaseSettings
from .database.database import DatabaseSingleton
from .locale import LanguageJP

# init database
settings = DatabaseSettings()
db = DatabaseSingleton.get_instance()
db.bind(**settings.dict_bind())
db.generate_mapping(create_tables=settings.create_tables)


class Mediator(BaseModel):
    storage: session_storage.SessionStorage

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)

        # 日付の初期化・取得
        self.storage.init_state(self.storage.key_date_selection.input, date.today())
        selected_date: date = self.storage.get_selected_date()

        # DBからデータを取得してstorageにセット
        self.storage.set_jobs(logic.Job.acquire_all())
        self.storage.set_job_records(
            logic.JobRecord.acquire_all_finished_by_date(selected_date)
        )
        self.storage.set_job_record_in_progress(
            logic.JobRecord.acquire_one_in_progress_by_date(selected_date)
        )
        self.storage.set_categories(logic.Category.acquire_all())
        self.storage.set_note(logic.Note.acquire_one_by_date(selected_date))

        # デフォルト言語設定
        self.storage.set_language(LanguageJP())

        # 初期化
        self.__init_message_area()

        # 状態変更
        self.__change_state_job_timer()
        self.__change_state_job_creation()
        self.__change_state_job_addition_manually()

    def __change_state_job_timer(self) -> None:
        disabled_selectbox: bool = True
        disabled_button_start: bool = True
        disabled_button_stop: bool = True

        # Determine whether each widget is disabled or not
        job_record_in_progress = self.storage.get_job_record_in_progress()
        jobs = self.storage.get_jobs()
        selected_date = self.storage.get_selected_date()
        if jobs != []:
            if job_record_in_progress is not None:
                # Set the working job to the selectbox
                self.storage.set_state(
                    self.storage.key_job_timer.selectbox,
                    job_record_in_progress.job,
                    do_init=True,
                )
                disabled_button_stop = False
            else:
                disabled_selectbox = False
                if selected_date == datetime.now().date():
                    disabled_button_start = False

        # Set disable or not
        self.storage.set_state(
            self.storage.key_job_timer.selectbox_disabled,
            disabled_selectbox,
            do_init=True,
        )
        self.storage.set_state(
            self.storage.key_job_timer.button_start_disabled,
            disabled_button_start,
            do_init=True,
        )
        self.storage.set_state(
            self.storage.key_job_timer.button_stop_disabled,
            disabled_button_stop,
            do_init=True,
        )

    def __change_state_job_creation(self) -> None:
        # Initialize
        self.storage.init_state(
            self.storage.key_job_creation.radio,
            session_storage.RadioJobCreation.job.value,
        )
        self.storage.init_state(self.storage.key_job_creation.checkbox, True)
        self.storage.init_state(self.storage.key_job_creation.checkbox_disabled, True)

        disabled_selectbox = True
        disabled_checkbox = True
        disabled_button = True

        value_radio = self.storage.get_state(self.storage.key_job_creation.radio)
        value_checkbox = self.storage.get_state(self.storage.key_job_creation.checkbox)
        categories = self.storage.get_categories()
        match value_radio:
            case session_storage.RadioJobCreation.job.value:
                if categories != []:
                    if not value_checkbox:
                        disabled_selectbox = False
                    disabled_checkbox = False
            case session_storage.RadioJobCreation.category.value:
                pass
            case _:
                # TODO: handle error properly
                raise Exception("!?!?!?")

        value_input = self.storage.get_state(self.storage.key_job_creation.input)
        if value_input:
            disabled_button = False

        self.storage.set_state(
            self.storage.key_job_creation.selectbox_disabled,
            disabled_selectbox,
            do_init=True,
        )
        self.storage.set_state(
            self.storage.key_job_creation.checkbox_disabled,
            disabled_checkbox,
            do_init=True,
        )
        self.storage.set_state(
            self.storage.key_job_creation.button_disabled, disabled_button, do_init=True
        )

    def __change_state_job_addition_manually(self) -> None:
        disabled_selectbox = True
        disabled_slider = True
        disabled_button = True

        selected_date = self.storage.get_selected_date()
        if selected_date == datetime.now().date():
            disabled_selectbox = False
            disabled_slider = False
            disabled_button = False

        self.storage.set_state(
            self.storage.key_job_addition_manually.selectbox_disabled,
            disabled_selectbox,
            do_init=True,
        )
        self.storage.set_state(
            self.storage.key_job_addition_manually.slider_disabled,
            disabled_slider,
            do_init=True,
        )
        self.storage.set_state(
            self.storage.key_job_addition_manually.button_disabled,
            disabled_button,
            do_init=True,
        )

    def __init_message_area(self) -> None:
        self.storage.init_state(self.storage.key_message_area.info, None)
        self.storage.init_state(self.storage.key_message_area.warn, None)
        self.storage.init_state(self.storage.key_message_area.error, None)
        self.storage.init_state(self.storage.key_message_area.exception, None)

    def __set_error(self, error: Exception) -> None:
        self.storage.set_state(self.storage.key_message_area.error, error)

    def click_today(self) -> None:
        self.storage.set_state(self.storage.key_date_selection.input, date.today())

    def click_start_job(self) -> None:
        job = self.storage.get_state(self.storage.key_job_timer.selectbox)
        logic.JobRecord.start(job.id)

    def click_stop_job(self) -> None:
        job_record_in_progress = self.storage.get_job_record_in_progress()
        if job_record_in_progress is None:
            raise Exception("!?!?!?")
        logic.JobRecord.stop(job_record_in_progress.id)

    def click_create_job_or_category(self) -> None:
        value_radio = self.storage.get_state(self.storage.key_job_creation.radio)
        value_input = self.storage.get_state(self.storage.key_job_creation.input)
        value_category = self.storage.get_state(self.storage.key_job_creation.selectbox)
        value_checkbox = self.storage.get_state(self.storage.key_job_creation.checkbox)

        try:
            match value_radio:
                case session_storage.RadioJobCreation.job.value:
                    if value_checkbox:
                        logic.Job.register(value_input)
                    else:
                        logic.Job.register(value_input, value_category.name)
                case session_storage.RadioJobCreation.category.value:
                    logic.Category.register(value_input)
                case _:
                    # TODO: handle error properly
                    raise Exception("!?!?!?")
        except logic.LogicException as error:
            self.__set_error(error)

    def click_add_job_record(self) -> None:
        job = self.storage.get_state(self.storage.key_job_addition_manually.selectbox)
        start_time, end_time = self.storage.get_state(
            self.storage.key_job_addition_manually.slider
        )
        try:
            logic.JobRecord.register(
                job.id,
                datetime.combine(self.storage.get_selected_date(), start_time),
                datetime.combine(self.storage.get_selected_date(), end_time),
            )
        except logic.LogicException as error:
            self.__set_error(error)

    def click_edit_job_log(
        self, key_selectbox: str, key_slider: str, job_record_id: int
    ) -> None:
        job = self.storage.get_state(key_selectbox)
        time_start, time_end = self.storage.get_state(key_slider)
        try:
            logic.JobRecord.revise(
                job_record_id,
                job.id,
                datetime.combine(self.storage.get_selected_date(), time_start),
                datetime.combine(self.storage.get_selected_date(), time_end),
            )
        except logic.LogicException as error:
            self.__set_error(error)

    def click_save_note(self) -> None:
        content = self.storage.get_state(self.storage.key_note_area.text_area)
        logic.Note.save(self.storage.get_selected_date(), content)

    def draw_message(self) -> None:
        self.storage.set_state(self.storage.key_message_area.info, None)
        self.storage.set_state(self.storage.key_message_area.warn, None)
        self.storage.set_state(self.storage.key_message_area.error, None)
        self.storage.set_state(self.storage.key_message_area.exception, None)

    class Config:
        allow_mutation = False
        arbitrary_types_allowed = True
        copy_on_model_validation = False
