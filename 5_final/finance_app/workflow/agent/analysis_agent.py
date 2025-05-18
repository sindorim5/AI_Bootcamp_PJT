from typing import Dict, Any
from workflow.agent.base_agent import BaseAgent
from workflow.state import AgentState


class AnalysisAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str):
        super().__init__(
            system_prompt=(
                "당신은 AI 금융 상담사 시스템의 분석 에이전트(Analysis Agent)입니다. "
                "MarketData Agent가 수집한 정량적 시세·지표와 "
                "Retrieve Agent가 검색한 뉴스·리포트를 종합 분석하여, "
                "사용자가 입력한 주제(topic), 자본금(capital), 위험성향(risk_level)을 바탕으로 "
                "투자자에게 유의미한 인사이트를 제공하세요."
            ),
            rag = rag,
            langfuse_session_id = langfuse_session_id
            )

    def _retrieve_context(self, state: AgentState) -> AgentState:

        if self.rag == False:
            return {**state, "agent_id": 3, "context": ""}

        market_docs   = state["market_data_docs"]
        retrieve_docs = state["retrieve_docs"]

        ctx = ""
        if market_docs:
            ctx += "[시장 데이터]\n" + super()._format_context(market_docs)

        if retrieve_docs:
            ctx += "\n[검색 결과]\n" + super()._format_context(retrieve_docs)

        return {
            **state,
            "agent_id": 3,
            "context": ctx
        }

    def _create_prompt(self, state: AgentState) -> str:
        topic = state["chat_state"]["topic"]
        capital = state["chat_state"]["capital"]
        risk_level = state["chat_state"]["risk_level"]
        context = state["context"]

        prompt = (
            f"'{topic}'에 대해, 자본금 {capital}만원, 위험성향 {risk_level} (1 ~ 5등급, 숫자가 클수록 공격투자형)투자자 관점에서\n"
            f"{context}\n"
            "위 정보를 바탕으로 주요 시장 추세, 기회와 리스크를 분석하고 "
            "투자자에게 유용한 인사이트를 제공하세요."
        )

        return prompt

