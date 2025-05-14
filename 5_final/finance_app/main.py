from database.session import db_session
import streamlit as st
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def init_session_state():
    return None

def render_ui():
    return None

if __name__ == "__main__":
    # init_session_state()

    db_session.initialize()

    # render_ui()
