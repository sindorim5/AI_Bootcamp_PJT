from typing import Dict, Any
from workflow.agent.base_agent import BaseAgent
from workflow.state import AgentState


class AnalysisAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str):
        super().__init__(
            system_prompt=(
                "You are the Analysis Agent in an AI financial advisor system. "
                "Synthesize the MarketData Agent’s quantitative data and the Retrieve Agent’s news/reports "
                "into decision-focused insights for a Korean investor.\n"
                "Rules:\n"
                "- Always answer in Korean.\n"
                "- Use only information contained in the provided context; do not fabricate missing data.\n"
                "- Preserve numbers/units/dates as shown; if dates exist, include them (YYYY-MM-DD).\n"
                "- No investment advice, recommendations, or price targets. Do not predict specific prices.\n"
                "- No URLs, no tables, no code blocks.\n"
                "- Avoid generic summaries; focus on why it matters and what could change.\n"
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
            f"사용자 프로필:\n"
            f"- 주제: '{topic}'\n"
            f"- 자본금: {capital}만원\n"
            f"- 위험성향: {risk_level} (1=보수적, 5=공격적)\n\n"
            "컨텍스트(두 블록 모두 참고):\n"
            f"{context}\n\n"
            "작성 지침:\n"
            "- 아래 컨텍스트에 근거한 사실만 사용하세요. 숫자·단위·날짜 표기를 그대로 유지하세요.\n"
            "- 일반적인 요약은 하지 말고, 투자자 관점에서 ‘왜 중요한지’와 ‘무엇이 변곡점이 되는지’에 집중하세요.\n"
            "- 주장/사실 옆에 근거가 필요한 경우 [문서 N] 형태로 간단히 표기하세요.\n"
            "- 확률은 정성적 표현(낮음/보통/높음)만 사용하고, 구체적 가격 목표나 매수/매도 권유는 금지합니다.\n\n"
            "다음 5개 섹션으로 한국어로만 작성하세요:\n"
            "1) 핵심 인사이트 (항목 3~6개, 각 한두 문장)\n"
            "2) 촉매·트리거 (조건/이벤트/지표)\n"
            "3) 시나리오(기준/상향/하향) — 조건 중심, 정성적 가능성(낮음/보통/높음)\n"
            "4) 모니터링 체크리스트 (추적할 지표·일정)\n"
            "5) 리스크 관리 관점에서 유의할 점 (행동 지시 아님, 고려사항)"
        )

        return prompt

