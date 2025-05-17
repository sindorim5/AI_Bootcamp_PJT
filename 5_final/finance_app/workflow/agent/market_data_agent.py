from base_agent import BaseAgent, AgentState
from retrieval.market_data_service import suggest_related_tickers, get_market_data
from typing import Dict, Any
from common.constants import Agent


class MarketDataAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str = None):
        super().__init__(
            system_prompt="당신은 금융 데이터 분석 전문가입니다. 사용자의 질문에 대해 시세 기반 인사이트를 제공하세요.",
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

        return {**state, "agent_id": 1, "context": context, "documents": documents}

    def _create_prompt(self, state: Dict[str, Any]) -> str:
        topic = state["topic"]
        context = state["context"]

        prompt = (
            f"'{topic}'에 대한 최근 시세 데이터와 지표는 다음과 같습니다:\n\n"
            f"{context}\n\n"
            "이 데이터를 바탕으로 사용자가 이해하기 쉽게 시장 상황을 분석해 주세요."
        )
        return prompt
