from typing import Dict, Any
from base_agent import BaseAgent
from state import AgentState
from retrieval.vector_store import search_topic


class RetrieveAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str):
        super().__init__(
            system_prompt=(
                "당신은 AI 금융 상담사 시스템의 전문 정보 검색 에이전트(Retrieve Agent)입니다. "
                "사용자가 입력한 주제(topic), 자본금(capital), 위험성향(risk_level)을 바탕으로 "
                "금융 뉴스·리포트를 검색하고, 핵심 내용을 정리해 제공하세요."
            ),
            rag = rag,
            langfuse_session_id = langfuse_session_id
            )

    def _retrieve_context(self, state: AgentState) -> AgentState:

        if self.rag == False:
            return {**state, "agent_id": 2, "context": ""}

        chat_state = state["chat_state"]
        topic = chat_state["topic"]
        capital = chat_state["capital"]
        risk_level = chat_state["risk_level"]

        documents = search_topic(
            topic=topic,
            capital=capital,
            risk_level=risk_level
            )

        context = super()._format_context(documents)

        return {
            **state,
            "agent_id": 2,
            "retrieve_docs": documents,
            "context": context,
            }

    def _create_prompt(self, state: AgentState) -> str:
        topic = state["chat_state"]["topic"]
        capital = state["chat_state"]["capital"]
        risk_level = state["chat_state"]["risk_level"]
        context = state["context"]

        prompt = (
            f"'{topic}'에 대해, 자본금 {capital}만원, 위험성향 {risk_level} (1 ~ 5등급, 숫자가 클수록 공격투자형)\n"
            "투자자에 관련 금융 뉴스·리포트 검색 결과입니다:\n\n"
            f"{context}\n\n"
            "위 내용을 바탕으로 핵심 사실과 인사이트를 요약해 주세요."
        )

        return prompt
