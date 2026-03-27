import os
import runpy
from pathlib import Path

import streamlit as st


APP_DIR = Path(__file__).resolve().parent
EMBED_ENV_VAR = 'STREAMLIT_EMBEDDED_DASHBOARD'

PAGES = {
    'Final Dashboard': {
        'file': 'market_dashboard.py',
        'description': 'Combined market overview plus stock analysis.',
    },
    'Prediction Dashboard': {
        'file': 'prediction_dashboard.py',
        'description': 'Model-based sentiment and prediction dashboard.',
    },
    'Legacy Stock Dashboard': {
        'file': 'stock_dashboard.py',
        'description': 'Older stock-only dashboard kept for comparison.',
    },
}


def run_embedded_page(filename: str) -> None:
    previous_value = os.environ.get(EMBED_ENV_VAR)
    os.environ[EMBED_ENV_VAR] = '1'

    try:
        runpy.run_path(str(APP_DIR / filename), run_name='__main__')
    finally:
        if previous_value is None:
            os.environ.pop(EMBED_ENV_VAR, None)
        else:
            os.environ[EMBED_ENV_VAR] = previous_value


st.set_page_config(
    page_title='Sentimental Drive Stock',
    page_icon='📈',
    layout='wide',
    initial_sidebar_state='expanded',
)

st.sidebar.title('Dashboard Launcher')
st.sidebar.caption('Run this file only: `streamlit run app/app.py`')

selected_page = st.sidebar.radio(
    'Choose the dashboard view',
    list(PAGES.keys()),
    index=0,
)

page_config = PAGES[selected_page]

st.sidebar.markdown('**Selected View**')
st.sidebar.write(selected_page)
st.sidebar.caption(page_config['description'])

if selected_page != 'Final Dashboard':
    st.info(
        'The default final result is "Final Dashboard". '
        'The other two options are preserved as alternate views.'
    )

run_embedded_page(page_config['file'])
