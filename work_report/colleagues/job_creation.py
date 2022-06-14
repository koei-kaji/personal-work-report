import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ..mediator import Mediator
from ..session_storage import SessionStorage


def job_creation(
    gen: DeltaGenerator,
    storage: SessionStorage,
    mediator: Mediator,
) -> None:

    with gen.expander(storage.get_language().job_creation_expander):
        st.radio(
            storage.get_language().job_creation_radio,
            key=storage.key_job_creation.radio,
            options=storage.job_creation_radio_values,
            horizontal=True,
        )
        st.selectbox(
            storage.get_language().job_creation_selectbox,
            key=storage.key_job_creation.selectbox,
            options=storage.get_categories(),
            disabled=storage.get_state(storage.key_job_creation.selectbox_disabled),
        )
        st.checkbox(
            storage.get_language().job_creation_checkbox,
            key=storage.key_job_creation.checkbox,
            disabled=storage.get_state(storage.key_job_creation.checkbox_disabled),
            # on_change=mediator.change_checkbox_not_select_category,
        )
        st.text_input(
            storage.get_language().job_creation_text_input,
            key=storage.key_job_creation.input,
        )
        st.button(
            storage.get_language().job_creation_button,
            key=storage.key_job_creation.button,
            on_click=mediator.click_create_job_or_category,
            disabled=storage.get_state(storage.key_job_creation.button_disabled),
        )
