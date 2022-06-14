import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ..mediator import Mediator
from ..session_storage import SessionStorage


def job_logs(
    gen: DeltaGenerator,
    storage: SessionStorage,
    mediator: Mediator,
) -> None:
    for i, job_record in enumerate(storage.get_job_records()):
        key_selectbox = f"{storage.key_job_logs.selectbox}_{i}"
        key_slider = f"{storage.key_job_logs.slider}_{i}"
        key_button = f"{storage.key_job_logs.button}_{i}"

        with gen.expander(str(job_record), expanded=False):
            st.selectbox(
                storage.get_language().job_logs_selectbox,
                key=key_selectbox,
                options=storage.get_jobs(),
                index=storage.get_jobs().index(job_record.job),
            )

            time_start = job_record.start.time()
            time_end = job_record.end.time()  # type: ignore[union-attr]
            st.slider(
                storage.get_language().job_logs_slider,
                key=key_slider,
                value=(time_start, time_end),
            )
            st.button(
                storage.get_language().job_logs_button,
                key=key_button,
                on_click=mediator.click_edit_job_log,
                args=(key_selectbox, key_slider, job_record.id),
            )
