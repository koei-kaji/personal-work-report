from datetime import datetime, time
from typing import Tuple, TypedDict

import pandas as pd
from plotly import express as px
from streamlit.delta_generator import DeltaGenerator

from ..session_storage import SessionStorage


class FigDict(TypedDict):
    job_id: int
    job: str
    start: datetime
    end: datetime
    status: str


def timeline_chart(
    gen: DeltaGenerator,
    storage: SessionStorage,
) -> None:

    job_records = storage.get_job_records()
    job_record_in_progress = storage.get_job_record_in_progress()

    dict_job_records = [
        FigDict(
            # TODO: 長い場合に備えてリミット設けて...表記
            job_id=job_record.job.id,
            job=str(job_record.job),
            start=job_record.start,
            end=job_record.end,  # type: ignore[typeddict-item]
            status="Finished",
        )
        for job_record in job_records
    ]

    if job_record_in_progress is not None:
        dict_job_record = FigDict(
            # TODO: 長い場合に備えてリミット設けて...表記
            job_id=job_record_in_progress.job.id,
            job=str(job_record_in_progress.job),
            start=job_record_in_progress.start,
            end=datetime.now(),
            status="InProgress",
        )
        dict_job_records.append(dict_job_record)

    if dict_job_records == []:
        return

    df = pd.DataFrame(dict_job_records)

    fig = px.timeline(
        df,
        x_start="start",
        x_end="end",
        y="job",
        color="status",
    )

    selected_date = storage.get_selected_date()
    scheduled_working_time: Tuple[time, time] = storage.get_state(
        storage.key_working_hours_schedule.slider
    )
    scheduled_working_datetime = (
        datetime.combine(selected_date, scheduled_working_time[0]),
        datetime.combine(selected_date, scheduled_working_time[1]),
    )
    fig.add_vline(x=scheduled_working_datetime[0])
    fig.add_vline(x=scheduled_working_datetime[1])
    gen.plotly_chart(
        fig, key=storage.key_timeline_chart.chart, use_container_width=True
    )
