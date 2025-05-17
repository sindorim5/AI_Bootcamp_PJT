import streamlit as st
import logging
from controller.conv_controller import ConvController


logger = logging.getLogger(__name__)

convController = ConvController()

def render_new_tab():

    with st.form("new_conv_form", border=False):
        # 대화 주제 입력
        topic = st.text_input(
            label="대화 주제를 입력하세요",
            placeholder="ex) 주식 투자에 대해 이야기해줘",
            key="input_topic"
        )

        st.checkbox(
            "RAG 활성화",
            value=True,
            help="외부 지식을 검색하여 토론에 활용합니다.",
            key="enable_rag",
        )

        submit_btn = st.form_submit_button("대화 시작")

        if submit_btn:
            logger.info("대화 시작 버튼 클릭")

            try:
                logger.info("대화 주제: %s", st.session_state.get("input_topic"))
                logger.info("대화 주제: %s", st.session_state.get("user_name"))
                logger.info("대화 주제: %s", st.session_state.get("capital"))
                logger.info("대화 주제: %s", st.session_state.get("risk_level"))

                result = start_session()
                if result:
                    None
                else:
                    st.error("대화 시작 실패")
            except ValueError as ve:
                logger.error(f"ValueError in on_new_conv_btn: {ve}")
                st.session_state["input_topic_err"] = str(ve)

        if st.session_state.get("input_topic_err", "") != "":
            st.error(st.session_state["input_topic_err"])
            st.session_state["input_topic_err"] = ""


def start_session(topic: str) -> bool:
    # input 검증
    clean_topic = topic.replace(" ", "")

    if not clean_topic:
        raise ValueError("공백은 사용할 수 없습니다.")

    # DB, session에 대화 주제 저장
    result = convController.on_new_conv_btn()

    if result:
        return True
    else:
        return False
