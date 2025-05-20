from typing import Dict, List, TypedDict, Any
from common.constants import Agent
from langchain_core.messages import BaseMessage
from langchain.schema import Document


class AgentType:
    @classmethod
    def to_korean(cls, role: str) -> str:
        if Agent.Analysis == role:
            return "분석"
        elif Agent.MarketData == role:
            return "시장 데이터"
        elif Agent.Retrieve == role:
            return "정보 검색"
        elif Agent.Portfolio == role:
            return "포트폴리오"
        else:
            return role

class ChatState(TypedDict):
    topic: str           # 사용자의 질문 주제 (ex. "반도체 산업 전망")
    user_name: str       # 사용자 이름
    capital: float       # 투자 자본금 (만원 단위 등)
    risk_level: int      # 위험 성향 (1 ~ 5 등급)

class AgentState(TypedDict):
    chat_state: Dict[str, Any]       # 사용자 입력 정보
    agent_id: int                    # 현재 실행 중인 Agent ID

    # MarketDataAgent 결과
    market_data_docs: List[Document] # 수집된 시세/지표 데이터 문서들
    market_data_response: str        # MarketDataAgent의 LLM 해석 결과

    # RetrieverAgent 결과
    retrieve_docs: List[Document]    # 수집된 뉴스/리포트 문서들
    retrieve_response: str           # RetrieverAgent의 요약/해석 결과

    # AnalysisAgent 결과
    analysis_response: str           # MarketData + Retrieve를 해석한 종합 분석

    # PortfolioAgent 결과
    portfolio_response: str          # 자산배분 시나리오 제안 결과

    # Agent 실행 시 사용하는 임시 필드 (LLM 프롬프트용)
    context: str                     # 이번 Agent에서 전달할 context (docs 요약 등)
    messages: List[BaseMessage]      # 이번 Agent에서 전달할 LLM messages
    response: str                    # 이번 Agent에서 받은 LLM 응답
