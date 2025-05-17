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
    topic: str
    user_name: str
    capital: float
    risk_level: int
    session_id: int
    session_seq: int

class AgentState(TypedDict):
    chat_state: Dict[str, Any]  # 사용자 입력
    agent_id: int               # Agent 역할 (분석, 시장 데이터, 정보 검색 등)
    context: str                # retrieve_context에서 수집된 doc를 정리, LLM에 전달할 메시지
    messages: List[BaseMessage] # prepare_messages에서 생성된 메시지
    response: str               # generate_response에서 생성된 LLM의 응답
    documents: List[Document]   # retrieve_context에서 검색된 문서
