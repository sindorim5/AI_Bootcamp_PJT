import streamlit as st
from database.session import db_session
from controller.main_controller import mainController
from common import constants
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # init session state
    if "app_mode" not in st.session_state:
        st.session_state["app_mode"] = constants.Mode.Application

    if "db_initialized" not in st.session_state:
        db_session.initialize()
        st.session_state["db_initialized"] = True


    mainController.start_app()
