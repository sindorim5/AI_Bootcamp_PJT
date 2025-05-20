import streamlit as st
import logging
from controller.user_controller import userController

logger = logging.getLogger(__name__)



def render_user_tab():
    default_user_name = st.session_state.get("user_name", "")
    default_capital = float(st.session_state.get("capital", 10.0))
    default_risk_level = st.session_state.get("risk_level", 3)

    with st.form("user_form", border=False):

        user_name = st.text_input(
            label="이름",
            placeholder="이름을 입력하세요.",
            help="공백 제외 최대 10자 이내",
            max_chars=10,
            value=default_user_name,
            key="input_user_name",
        )

        capital = st.number_input(
            label="자본금 (만원)",
            min_value=10.0,
            step=1.0,
            format="%0f",
            value=default_capital,
            key="input_capital"
        )

        risk_level = st.slider(
                "투자 성향",
                min_value=1,
                max_value=5,
                help="1: 안정형, 5: 공격투자형",
                value=default_risk_level,
                key="input_risk_level"
            )

        save_btn = st.form_submit_button("저장")
        load_btn = st.form_submit_button("불러오기")

        if save_btn:
            result = save_user_info(user_name, capital, risk_level)
            if result:
                st.success("저장 성공")
            else:
                st.error("저장 실패")

        if load_btn:
            result = load_user_info(user_name)
            if result:
                st.success("불러오기 성공")
            else:
                st.error("불러오기 실패")


    if (
        st.session_state.get("user_name")
        and st.session_state.get("capital") is not None
        and st.session_state.get("risk_level") is not None
    ):
        st.markdown(f"""
        ### 사용자 정보

        - **이름:** {st.session_state['user_name']}
        - **자본금:** {st.session_state['capital']:.0f}만원
        - **투자성향:** {st.session_state['risk_level']}점
        """)
    else:
        st.markdown(
            """
            ### 사용자 정보
            - 이름을 입력하여 사용자 정보를 저장 혹은 불러와주세요.
            """
        )

def save_user_info(user_name: str, capital: float, risk_level: int) -> bool:
    # input 검증
    clean_name = user_name.replace(" ", "")

    if not clean_name:
        st.error("공백은 사용할 수 없습니다.")
        return False
    elif len(clean_name) != len(user_name):
        st.error("공백은 사용할 수 없습니다.")
        return False

    # DB, session에 사용자 정보 저장
    result = userController.on_save_btn(user_name, capital, risk_level)
    if result:
        return True
    else:
        return False


def load_user_info(user_name: str) -> bool:

    clean_name = user_name.replace(" ", "")

    if not clean_name:
        st.error("공백은 사용할 수 없습니다.")
        return False
    elif len(clean_name) != len(user_name):
        st.error("공백은 사용할 수 없습니다.")
        return False

    try:
        # user_name으로 DB에서 사용자 정보 조회
        user = userController.on_load_btn(user_name)
        if user:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"load_user_info: {str(e)}")
        return False


