from typing import Dict, Any
from workflow.agent.base_agent import BaseAgent
from workflow.state import AgentState
from retrieval.vector_store import search_topic
import logging

logger = logging.getLogger(__name__)

class RetrieveAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str):
        super().__init__(
            system_prompt=(
                "You are the Retrieve Agent in an AI financial advisor system. "
                "Your role is to analyze retrieved financial news and reports "
                "based on the user's topic, capital, and risk level, and deliver "
                "a concise, factual summary in Korean. "
                "Rules:\n"
                "- Always answer in Korean.\n"
                "- Summarize only information supported by the retrieved documents.\n"
                "- Do not fabricate data. If data is missing, clearly state '정보 없음'.\n"
                "- Highlight key facts, market context, and investor-relevant insights.\n"
                "- Keep the output compact, structured, and easy to read for a busy investor."
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
            f"사용자 프로필:\n"
            f"- 주제: '{topic}'\n"
            f"- 자본금: {capital}만원\n"
            f"- 위험성향: {risk_level} (1=보수적, 5=공격적)\n\n"
            "다음은 관련 금융 뉴스·리포트 검색 결과입니다:\n\n"
            f"{context}\n\n"
            "Instructions:\n"
            "- 위 문서들에 근거하여 한국어로 요약하세요.\n"
            "- 1) 핵심 요약 (3~5문장)\n"
            "- 2) 주요 데이터 포인트 (불릿)\n"
            "- 3) 리스크 및 모니터링 포인트 (불릿)\n"
            "- 문서에 없는 내용은 추가하지 마세요."
        )

        return prompt
