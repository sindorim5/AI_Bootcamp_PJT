import streamlit as st
def render_new_tab():

    st.checkbox(
        "RAG 활성화",
        value=True,
        help="외부 지식을 검색하여 토론에 활용합니다.",
        key="enable_rag",
    )

    return None
