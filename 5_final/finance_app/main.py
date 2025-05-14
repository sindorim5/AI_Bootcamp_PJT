from database.session import db_session
import streamlit as st
import logging
from common import constants
from common import utils
from view import sidebar

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def init_session_state():
    return None

def render_ui():
    st.set_page_config(page_title="AI 금융 도우미", page_icon="💰")

    st.title("AI 금융 도우미")
    st.markdown(
        """
        ## 금융 관련 질문을 해보세요!
        - 투자성향과 자본금을 입력하면, 적합한 투자 분석을 제공합니다!
        """
    )

    sidebar.render_sidebar()

    return None

if __name__ == "__main__":
    # init_session_state()

    db_session.initialize()

    render_ui()
