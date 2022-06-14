from datetime import time
from typing import Tuple

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ..mediator import Mediator
from ..session_storage import SessionStorage


def job_addition_manually(
    gen: DeltaGenerator,
    storage: SessionStorage,
    mediator: Mediator,
    *,
    default: Tuple[time, time] | None = (time(9, 0), time(18, 0)),
) -> None:

    with gen.expander(
        storage.get_language().job_addition_manually_expander, expanded=True
    ):
        st.selectbox(
            storage.get_language().job_addition_manually_selectbox,
            key=storage.key_job_addition_manually.selectbox,
            options=storage.get_jobs(),
            disabled=storage.get_state(
                storage.key_job_addition_manually.selectbox_disabled
            ),
        )
        st.slider(
            storage.get_language().job_addition_manually_slider,
            key=storage.key_job_addition_manually.slider,
            value=default,
            disabled=storage.get_state(
                storage.key_job_addition_manually.slider_disabled
            ),
        )
        st.button(
            storage.get_language().job_addition_manually_button,
            key=storage.key_job_addition_manually.button,
            on_click=mediator.click_add_job_record,
            disabled=storage.get_state(
                storage.key_job_addition_manually.button_disabled
            ),
        )
