from streamlit.delta_generator import DeltaGenerator

from ..mediator import Mediator
from ..session_storage import SessionStorage


def date_selection(
    gen: DeltaGenerator, storage: SessionStorage, mediator: Mediator
) -> None:

    gen.date_input(
        storage.get_language().date_selection_date_input,
        key=storage.key_date_selection.input,
    )
    gen.button(
        storage.get_language().date_selection_button,
        key=storage.key_date_selection.button,
        on_click=mediator.click_today,
    )
