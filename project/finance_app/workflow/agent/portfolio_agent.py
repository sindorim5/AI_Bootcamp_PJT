from typing import Dict, Any
from workflow.agent.base_agent import BaseAgent
from workflow.state import AgentState


class PortfolioAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str):
        super().__init__(
            system_prompt=(
                "당신은 AI 금융 상담사 시스템의 포트폴리오 에이전트(Portfolio Agent)입니다. "
                "MarketData Agent와 Retrieve Agent, Analysis Agent의 결과를 바탕으로 "
                "사용자의 자본금과 위험성향을 고려한 투자 시나리오별 자산배분 계획을 제안하세요."
            ),
            rag = rag,
            langfuse_session_id = langfuse_session_id
        )

    def _retrieve_context(self, state: AgentState) -> AgentState:

        if self.rag == False:
            return {**state, "agent_id": 4, "context": ""}

        market_docs   = state["market_data_docs"]
        retrieve_docs = state["retrieve_docs"]
        analysis = state["analysis_response"]

        ctx = ""

        if market_docs:
            ctx += "[시장 데이터]\n" + super()._format_context(market_docs)
        if retrieve_docs:
            ctx += "\n[검색 결과]\n" + super()._format_context(retrieve_docs)
        if analysis:
            ctx += "\n[분석 결과]\n" + super()._format_context(analysis)

        return {
            **state,
            "agent_id": 4,
            "context": ctx
        }

    def _create_prompt(self, state: AgentState) -> str:
        topic = state["chat_state"]["topic"]
        capital = state["chat_state"]["capital"]
        risk_level = state["chat_state"]["risk_level"]
        context = state["context"]

        prompt = (
            f"'{topic}'에 대해, 자본금 {capital}만원, 위험성향 {risk_level}등급 "
            f"(1~5, 숫자가 클수록 공격투자형) 기준으로\n\n"
            f"{context}\n\n"
            "위 정보를 바탕으로 다음을 마크다운 표로 제시해 주세요:\n"
            "- 자산군: 국내 주식, 해외 주식, 채권, 대체투자(ETF 등)\n"
            "- 각 자산군별 비율(%)\n"
            "- 각 자산군별 세부 종목 (예: 삼성전자, QQQ, 미국 10년물 국채, GLD 등)\n\n"
            "표 아래에는 한두 문장으로 간단한 설명을 덧붙여 주세요."
        )

        return prompt

