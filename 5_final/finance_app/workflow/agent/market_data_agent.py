from workflow.agent.base_agent import BaseAgent
from workflow.state import AgentState
from retrieval.market_data_service import suggest_related_tickers, get_market_data
from typing import Dict, Any
from common.constants import Agent


class MarketDataAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str):
        super().__init__(
            system_prompt=(
                "당신은 숙련된 금융 데이터 분석가(MarketData Agent)입니다. "
                "사용자가 입력한 주제(topic), 자본금(capital), 위험성향(risk_level)을 바탕으로 "
                "yfinance-기반 시세, 주요 지수, 금리, 환율 등의 정량적 마켓 데이터를 수집하고, "
                "이를 사람이 읽기 편한 요약 형태로 가공하여 제공하세요. "
                "• 종목별 현재가, 등락률을 포함하고\n"
                "• 지수(S&P500, KOSPI 등)와 환율·금리 동향을 포함하며\n"
                "• 필요한 경우 간단한 해석(예: “최근 3개월간 상승세” 등)을 덧붙이세요. "
                "응답은 오직 포맷에 맞는 텍스트로만 반환하고, 불필요한 설명이나 예시는 생략하세요."
            ),
            rag = rag,
            langfuse_session_id = langfuse_session_id
            )

    def _retrieve_context(self, state: AgentState) -> AgentState:

        if self.rag == False:
            return {**state, "agent_id": 1, "context": ""}

        chat_state = state["chat_state"]
        topic = chat_state["topic"]
        capital = chat_state["capital"]
        risk_level = chat_state["risk_level"]

        tickers = suggest_related_tickers(topic, capital, risk_level)
        documents = get_market_data(tickers)

        context = super()._format_context(documents)

        return {
            **state,
            "agent_id": 1,
            "market_data_docs": documents,
            "context": context,
            }

    def _create_prompt(self, state: AgentState) -> str:
        topic = state["chat_state"]["topic"]
        capital = state["chat_state"]["capital"]
        risk_level = state["chat_state"]["risk_level"]
        context = state["context"]

        prompt = (
            f"'{topic}'에 대해, 자본금 {capital}만원, 위험성향 {risk_level} (1 ~ 5등급, 숫자가 클수록 공격투자형)\n"
            "투자자에 대한 최근 시세 데이터와 지표는 다음과 같습니다:\n\n"
            f"{context}\n\n"
            "이 데이터를 바탕으로 사용자가 이해하기 쉽게 시장 상황을 분석해 주세요."
        )
        return prompt
