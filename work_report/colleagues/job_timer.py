from streamlit.delta_generator import DeltaGenerator

from ..mediator import Mediator
from ..session_storage import SessionStorage


# TODO: 現在の実行状況も確認できると良い
def job_timer(
    gen: DeltaGenerator,
    storage: SessionStorage,
    mediator: Mediator,
) -> None:

    gen.selectbox(
        storage.get_language().job_timer_selectbox,
        key=storage.key_job_timer.selectbox,
        options=storage.get_jobs(),
        disabled=storage.get_state(storage.key_job_timer.selectbox_disabled),
    )
    gen.button(
        storage.get_language().job_timer_button_start,
        key=storage.key_job_timer.button_start,
        disabled=storage.get_state(storage.key_job_timer.button_start_disabled),
        on_click=mediator.click_start_job,
    )
    gen.button(
        storage.get_language().job_timer_button_stop,
        key=storage.key_job_timer.button_stop,
        disabled=storage.get_state(storage.key_job_timer.button_stop_disabled),
        on_click=mediator.click_stop_job,
    )
