from streamlit.delta_generator import DeltaGenerator

from ..mediator import Mediator
from ..session_storage import SessionStorage


def message_area(
    gen: DeltaGenerator,
    storage: SessionStorage,
    mediator: Mediator,
) -> None:
    info = storage.get_state(storage.key_message_area.info)
    if info:
        gen.info(info)

    warn = storage.get_state(storage.key_message_area.warn)
    if warn:
        gen.warning(warn)

    error = storage.get_state(storage.key_message_area.error)
    if error:
        gen.error(error)

    exception = storage.get_state(storage.key_message_area.exception)
    if exception:
        gen.exception(error)

    mediator.draw_message()
