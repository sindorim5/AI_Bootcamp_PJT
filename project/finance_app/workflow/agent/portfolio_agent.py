from typing import Dict, Any
from workflow.agent.base_agent import BaseAgent
from workflow.state import AgentState


class PortfolioAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str):
        super().__init__(
                "You are the Portfolio Agent in an AI financial advisor system. "
                "Using the MarketData, Retrieve, and Analysis outputs provided in the context, "
                "propose scenario-based asset allocation plans tailored to the user's capital and risk level.\n"
                "Rules:\n"
                "- Always answer in Korean.\n"
                "- Provide allocations for three scenarios: 보수적, 중립적, 공격적.\n"
                "- Rows: 국내 주식, 해외 주식, 채권, 대체투자(ETF 등). Columns: 보수적, 중립적, 공격적.\n"
                "- Percentages in each column must sum to exactly 100 (no units, integers preferred; if needed one decimal).\n"
                "- Include 2~4 example instruments per asset class (e.g., 삼성전자, QQQ, 미국 10년물 국채, GLD). "
                "Prefer instruments mentioned in the context; if none, provide representative examples and mark them as 예시.\n"
                "- Ground your rationale in the provided context; do not invent facts or cite external data. No URLs.\n"
                "- No investment advice or guarantees; do not give price targets.\n"
                "- After the table, add a brief one- or two-sentence explanation connecting the allocation to the user's risk level and current market context."
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
        f"사용자 프로필:\n"
        f"- 주제: '{topic}'\n"
        f"- 자본금: {capital}만원\n"
        f"- 위험성향: {risk_level} (1=보수적, 5=공격적)\n\n"
        "컨텍스트(시장 데이터, 검색 결과, 분석 결과 포함):\n"
        f"{context}\n\n"
        "작성 지침:\n"
        "- 아래 형식의 마크다운 표로만 자산배분을 제시하세요.\n"
        "- 행: 국내 주식, 해외 주식, 채권, 대체투자(ETF 등)\n"
        "- 열: 보수적 | 중립적 | 공격적\n"
        "- 각 열의 합계가 정확히 100이 되도록 %를 배분하세요(정수 우선, 필요 시 소수점 한 자리).\n"
        "- 각 자산군 셀에는 괄호로 2~4개의 세부 종목/ETF 예시를 제시하세요. "
        "컨텍스트에 등장한 종목을 우선 사용하고, 없으면 대표적 상품을 '예시'로 표기하세요.\n"
        "- 외부 사실을 새로 만들지 말고, 컨텍스트에서 유도 가능한 수준의 근거로만 작성하세요. URL·코드블록 금지.\n\n"
        "출력:\n"
        "1) 자산배분 마크다운 표 (보수적/중립적/공격적 컬럼 포함)\n"
        "2) 표 아래 한두 문장으로 본 배분이 사용자 위험성향 및 현재 시장 맥락과 어떻게 연결되는지 설명"
    )

        return prompt

