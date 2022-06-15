from streamlit.delta_generator import DeltaGenerator

from ..session_storage import SessionStorage


def language_selection(
    gen: DeltaGenerator,
    storage: SessionStorage,
) -> None:
    gen.selectbox(
        storage.get_language().language_selection_selectbox,
        key=storage.key_language_selection.selectbox,
        options=storage.get_languages(),
        index=storage.get_languages().index(storage.get_language()),
    )
