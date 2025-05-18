from database.repository.user_repository import user_repository
from database.repository.session_repository import session_repository
from database.model import User, Session
from database.session import db_session
from common.utils import dict_to_str
from common import constants
from workflow.state import AgentState
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

    def on_new_conv_btn(self, topic: str) -> bool:
        logger.info("ConvController on_new_conv_btn %s", topic)
        try:
            # 현재 input 검증
            if (
                not st.session_state.get("user_name")
                or st.session_state.get("capital") is None
                or st.session_state.get("risk_level") is None
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
                    topic=topic
                )
                st.session_state["topic"] = topic
                st.session_state["session_id"] = session_id
                st.session_state["app_mode"] = constants.Mode.Portfolio

                logger.info(st.session_state["topic"])
                logger.info(st.session_state["session_id"])
                logger.info(st.session_state["app_mode"])
                return True
        except RepositoryError as re:
            logger.error(f"RepositoryError in on_new_conv_btn: {re}")
            return False

    def insert_session_result(self, agentState: AgentState) -> bool:
        logger.info("ConvController insert_session_result")
        logger.info(agentState)
        try:
            session_id = st.session_state.get("session_id", "")
            user_name = st.session_state.get("user_name", "")
            capital = st.session_state.get("capital")
            risk_level = st.session_state.get("risk_level")
            topic = st.session_state.get("topic", "")

            if not session_id or not user_name or not capital or not risk_level or not topic:
                return
            else:
                user = user_repository.get_user_by_name(user_name)

                if user is None:
                    return

                agentState_str = dict_to_str(agentState)

                result = session_repository.create_session_detail(
                    session_id=session_id,
                    response=agentState_str
                )
                if result:
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"Error in insert_session_result: {e}")

    def on_history_detail_btn(self, session_id: int) -> Session:
        session_detail = session_repository.get_session_detail_by_id(session_id=session_id)
        return session_detail

    def on_history_detail_del_btn(self, session_id: int) -> bool:
        result1 = session_repository.delete_session_by_id(session_id)
        if result1:
            logger.info("detail 삭제 완료")

        result2 = session_repository.delete_session_detail_by_id(session_id)
        if result2:
            logger.info("session 삭제 완료")

        return True


convController = ConvController()
