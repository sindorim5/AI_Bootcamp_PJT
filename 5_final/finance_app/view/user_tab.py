import streamlit as st
import logging

logger = logging.getLogger(__name__)

def render_user_tab():
    default_user_name = st.session_state.get("user_name", "")
    default_capital = st.session_state.get("capital", 10.0)
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
            value=float(default_capital),
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
            result = load_user_info("test_user")
            if result:
                st.success("불러오기 성공")
            else:
                st.error("불러오기 실패")

def save_user_info(user_name: str, capital: float, risk_level: int) -> bool:
    try:
        clean_name = user_name.replace(" ", "")

        if not clean_name:
            st.error("공백은 사용할 수 없습니다.")
            return False
        elif len(clean_name) != len(user_name):
            st.error("공백은 사용할 수 없습니다.")
            return False

        st.session_state.update(
            {
                "user_name": user_name,
                "capital": capital,
                "risk_level": risk_level,

            }
        )
        logger.info("저장: %s / %d / %d", user_name, risk_level, capital)
        return True
    except Exception as e:
        logger.error(f"save_user_info: {str(e)}")
        return False

def load_user_info(user_name: str) -> bool:
    try:
        # user_name으로 DB에서 사용자 정보 조회
        capital = 999.0
        risk_level = 5

        st.session_state.update(
            {
                "user_name": user_name,
                "capital": capital,
                "risk_level": risk_level,
                "input_user_name": user_name,
                "input_capital": capital,
                "input_risk_level": risk_level
            }
        )

        if user_name and capital and risk_level:
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"load_user_info: {str(e)}")
        return False


