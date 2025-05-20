import streamlit as st
import logging
from controller.user_controller import userController
from database.repository.session_repository import session_repository
from database.repository.user_repository import user_repository
from controller.conv_controller import convController
from common.utils import parse_dtm
from common.constants import Mode

logger = logging.getLogger(__name__)

def render_history_tab():

    if st.session_state.get("sessions", "") != "":
        logger.info(st.session_state['sessions'])

        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("이력 새로고침", use_container_width=True):
                st.rerun()

        with col2:
            if st.button("전체 이력 삭제", type="primary", use_container_width=True):
                if st.session_state.get("user_name", "") != "":
                    user_name = st.session_state.get("user_name")
                    user = user_repository.get_user_by_name(user_name=user_name)
                    sessions = session_repository.get_session_by_user_id(user.user_id)

                    for s in sessions:
                        try:

                            result1 = session_repository.delete_session_detail_by_id(s.session_id)
                            if result1:
                                logger.info("detail 삭제 완료")
                            result2 = session_repository.delete_session_by_id(s.session_id)
                            if result2:
                                logger.info("session 삭제 완료")
                        except Exception as e:
                            logger.error(f"삭제 실패 {str(e)}")

        if st.session_state.get("user_name", "") != "":
            user_name = st.session_state.get("user_name")
            user = user_repository.get_user_by_name(user_name=user_name)
            sessions = session_repository.get_session_by_user_id(user.user_id)
            if sessions:
                render_history_list(sessions)

def render_history_list(sessions):
    for session in sessions:
        with st.container(border=True):

            st.write(f"***{session.topic}***")

            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                parsed_dtm = parse_dtm(session.audit_dtm)
                st.caption(f"날짜: {parsed_dtm} | 자본금: {session.capital} | 투자성향: {session.risk_level}")

            with col2:
                if st.button("보기", key=f"history_{session.session_id}", use_container_width=True):
                    session_detail = convController.on_history_detail_btn(session.session_id)
                    if session_detail:
                        st.session_state.update({
                            "app_mode": Mode.History,
                            "history_session": session,
                            "history_session_dtl": session_detail
                            })

            with col3:
                if st.button("삭제", key=f"del_{session.session_id}", use_container_width=True):
                    convController.on_history_detail_del_btn(session.session_id)
                    st.rerun()
