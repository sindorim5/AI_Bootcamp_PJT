import streamlit as st
import logging
from langchain.schema import Document
from typing import List, Any, Optional
from workflow.state import AgentState
from common.constants import Mode, Agent
from controller.conv_controller import convController
from common.utils import str_to_agentState
from view import sidebar


logger = logging.getLogger(__name__)

def render_application():
    st.set_page_config(page_title="AI 금융 상담사", page_icon="💰")
    st.title("💰 AI 금융 상담사")
    st.markdown(
        """
        ## 금융 관련 질문을 해보세요!
        - 투자성향과 자본금을 입력하면, 적합한 투자 분석을 제공합니다!
        """
    )

def render_portfolio(stream_gen):
    node_output_body = None

    with st.spinner("AI 금융 상담을 진행 중입니다… 잠시 기다려주세요"):
        for chunk in stream_gen:
            body = render_portfolio_chunk(chunk)
            if body:
                node_output_body = body
            # DB 저장

        if node_output_body:
            convController.insert_session_result(node_output_body)
            render_source_materials(node_output_body)

    logger.info("end of render_portfolio")


def render_portfolio_chunk(chunk):
    if not chunk:
        return

    node = chunk[0] if len(chunk) > 0 else None
    if not node or node == ():
        return

    node_name = chunk[0][0].partition(':')[0]
    node_output = chunk[1]
    node_output_body = node_output.get("generate_response", None)

    if node_output_body:
        if node_name == Agent.MarketData:
            response = node_output_body.get("market_data_response", None)
        elif node_name == Agent.Retrieve:
            response = node_output_body.get("retrieve_response", None)
        elif node_name == Agent.Analysis:
            response = node_output_body.get("analysis_response", None)
        elif node_name == Agent.Portfolio:
            response = node_output_body.get("portfolio_response", None)

        render_chat_message(node_name, response)

        return node_output_body if node_name == Agent.Portfolio else None


def render_chat_message(node_name: str, response: Optional[str]):
    with st.chat_message(node_name, avatar=Agent.to_avatar(node_name)):
        st.markdown(f"""### {Agent.to_korean(node_name)}""")

        st.markdown(response)


def render_source_materials(node_output_body: AgentState):
    logger.info("render_source_materials")
    with st.expander("사용된 참고 자료 보기"):
        st.subheader(f"시장 데이터 자료")
        for i, doc in enumerate(node_output_body.get("market_data_docs", [])):
            st.markdown(f"#### 문서 {i + 1}")
            if doc.page_content:
                st.markdown(doc.page_content)
            st.divider()

        st.subheader(f"정보 검색 자료")
        for i, doc in enumerate(node_output_body.get("retrieve_docs", [])):
            st.markdown(f"#### 문서 {i + 1}")
            if doc.page_content:
                st.markdown(doc.page_content)
            source = doc.metadata.get("source")
            if source:
                st.markdown(f"- 출처: {source}")
            st.divider()


def render_history_view():
    logger.info("render_history_view")
    session = st.session_state.get("history_session", None)
    session_detail = st.session_state.get("history_session_dtl", None)

    if session and session_detail:
        response_str = session_detail.response
        agentState = str_to_agentState(response_str)
        for i in [1, 2, 3, 4]:
            node_name = ""
            if i == 1:
                node_name = Agent.MarketData
            elif i == 2:
                node_name = Agent.Retrieve
            elif i == 3:
                node_name = Agent.Analysis
            else:
                node_name = Agent.Portfolio

            if node_name == Agent.MarketData:
                response = agentState.get("market_data_response", None)
            elif node_name == Agent.Retrieve:
                response = agentState.get("retrieve_response", None)
            elif node_name == Agent.Analysis:
                response = agentState.get("analysis_response", None)
            elif node_name == Agent.Portfolio:
                response = agentState.get("portfolio_response", None)

            render_chat_message(node_name, response)
        render_source_materials(agentState)

def render_ui():
    render_application()
    sidebar.render_sidebar()
