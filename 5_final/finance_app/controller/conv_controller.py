from database.repository.user_repository import user_repository
from database.repository.session_repository import session_repository
from database.model import User, Session
from database.session import db_session
from common import constants
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    pass

class ConvController:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConvController, cls).__new__(cls)
        return cls._instance

    def on_new_conv_btn(self) -> bool:
        logger.debug("ConvController on_new_conv_btn")
        try:
            # 현재 input 검증
            if (
                st.session_state.get("user_name")
                and st.session_state.get("capital") is not None
                and st.session_state.get("risk_level") is not None
            ):
                raise ValueError("사용자 정보를 입력해주세요.")
            elif st.session_state.get("input_topic", "") == "":
                raise ValueError("대화 주제를 입력해주세요.")

            user = user_repository.get_user_by_name(st.session_state["user_name"])
            if user is None:
                raise ValueError("사용자 정보를 입력해주세요.")
            else:
                session_id = session_repository.create_session(
                    user=user,
                    topic=st.session_state["input_topic"]
                )
                st.session_state["session_id"] = session_id
                st.session_state["app_mode"] = constants.Mode.Portfolio
                # Agent 수행
        except RepositoryError as re:
            logger.error(f"RepositoryError in on_new_conv_btn: {re}")
            return False

    def start_agent(self):
        return None
