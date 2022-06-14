from streamlit.delta_generator import DeltaGenerator

from ..mediator import Mediator
from ..session_storage import SessionStorage


def note_area(
    gen: DeltaGenerator,
    storage: SessionStorage,
    mediator: Mediator,
) -> None:
    note = storage.get_note()
    content: str = ""
    if note is not None and note.content is not None:
        content = note.content

    gen.text_area(
        storage.get_language().note_area_text_area,
        key=storage.key_note_area.text_area,
        value=content,
        height=300,
    )
    gen.button(
        storage.get_language().note_area_button,
        key=storage.key_note_area.button,
        on_click=mediator.click_save_note,
    )
