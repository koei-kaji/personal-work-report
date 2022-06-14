import streamlit as st

from work_report import colleagues as col
from work_report.mediator import Mediator
from work_report.session_storage import SessionStorage

# --------- init context & mediator -------------- #
storage = SessionStorage(
    state=st.session_state,
)
mediator = Mediator(storage=storage)

# --------- init streamlit-------------- #
st.set_page_config(page_title=storage.get_language().main_page_title, layout="wide")
st.title(storage.get_language().main_title)


# --------- construct -------------- #
# TODO: configで読み込んで配置をカスタマイズできるようにする
row_1 = st.columns([1])
row_2 = st.columns([1, 1])
row_3 = st.columns([2, 1])
row_4 = st.columns([1, 1])

col.message_area(row_1[0], storage, mediator)
col.date_selection(row_2[0], storage, mediator)
col.working_hours_schedule(row_2[1], storage)
col.timeline_chart(
    row_3[0],
    storage,
)
col.job_timer(
    row_3[1],
    storage,
    mediator,
)

col.job_addition_manually(
    row_3[1],
    storage,
    mediator,
)
col.job_creation(
    row_3[1],
    storage,
    mediator,
)
col.job_logs(
    row_4[0],
    storage,
    mediator,
)
col.note_area(row_4[1], storage, mediator)
