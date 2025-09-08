from workflow.agent.base_agent import BaseAgent
from workflow.state import AgentState
from retrieval.market_data_service import suggest_related_tickers, get_market_data
from typing import Dict, Any
from common.constants import Agent


class MarketDataAgent(BaseAgent):
    def __init__(self, rag: bool, langfuse_session_id: str, plan_enabled: bool = False):
        super().__init__(
            system_prompt=(
                "You are the MarketData Agent in an AI financial advisor system. "
                "You will be given pre-fetched yfinance-based quotes for stocks/ETFs and macro indicators "
                "(indices, interest rates, FX, commodities) in the message context. "
                "Transform that raw context into a concise, investor-ready summary.\n"
                "Rules:\n"
                "- Always answer in Korean.\n"
                "- Use only the provided context; do not invent or assume missing data.\n"
                "- Keep numbers/currencies/percentages exactly as shown; do not re-annualize or guess dates.\n"
                "- No URLs, no tables, no code blocks, no extra commentary.\n"
                "- Be neutral and factual; no predictions.\n"
                "- In '종목 스냅샷' [section: stock], and in '주요 지표 스냅샷' [section: macro]\n"
                "- Each snapshot should be like '- metadata.ticker(or metadata.indicator) (metadata.name): metadata.price, metadata.change'\n"
                "Output format:\n"
                "1) 종목 스냅샷\n"
                "2) 주요 지표 스냅샷\n"
                "3) 핵심 코멘트 (2~4문장)\n"
            ),
            rag = rag,
            langfuse_session_id = langfuse_session_id,
            plan_enabled = plan_enabled
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
            f"사용자 프로필:\n"
            f"- 주제: '{topic}'\n"
            f"- 자본금: {capital}만원\n"
            f"- 위험성향: {risk_level} (1=보수적, 5=공격적)\n\n"
            "아래는 yfinance 기반으로 수집된 최근 시세/지표 컨텍스트입니다.:\n\n"
            f"{context}\n\n"
            "작성 지침:\n"
            "- 위 컨텍스트에 포함된 정보만 사용하세요.\n"
            "- 숫자·통화 단위·등락률 표기를 그대로 유지하세요.\n"
            "- 소수점이 있다면 2자리까지 표시하세요"
            "- '종목 스냅샷'에는 [section: stock] 항목을, '주요 지표 스냅샷'에는 [section: macro] 항목을 요약하세요.\n"
            "- 각 스냅샷 항목은 다음 형식을 따르세요: '- TICKER(또는 INDICATOR) (name): 현재가, 변동률'\n"
            "- 예시) 'SOXX (iShares Semiconductor ETF): 245.32 USD, 변동률: -1.45%'\n"
            "- 중복 내용은 한 번만 언급하세요. 예측/투자권유는 금지합니다.\n\n"
            "- 다음 섹션으로 한국어로만 출력하고 각 세부 항목들은 예시의 형식을 꼭 지켜주세요:\n"
            "1) 종목 스냅샷\n"
            "2) 주요 지표 스냅샷\n"
            "3) 핵심 코멘트 (2~4문장)\n"
        )
        return prompt
