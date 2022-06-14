from datetime import time
from typing import Tuple

from streamlit.delta_generator import DeltaGenerator

from ..session_storage import SessionStorage


def working_hours_schedule(
    gen: DeltaGenerator,
    storage: SessionStorage,
    *,
    default: Tuple[time, time] | None = (time(9, 0), time(18, 0)),
) -> None:
    gen.slider(
        storage.get_language().working_hours_schedule_slider,
        key=storage.key_working_hours_schedule.slider,
        value=default,
    )
