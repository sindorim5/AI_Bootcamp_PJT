from enum import Enum

class Tab(Enum):
    My = "내 정보"
    New = "새 대화"
    History = "대화 내역"

class Mode(Enum):
    Application = "application" # default
    Portfolio = "portfolio"     # 포트폴리오 생성 요청 시
    History = "history"         # 대화 내역 요청 시

class Agent:
    Analysis = "analysis"
    MarketData = "market_data"
    Portfolio = "portfolio"
    Retrieve = "retrieve"

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

    @classmethod
    def to_avatar(cls, role: str) -> str:
        if Agent.Analysis == role:
            return "📊"
        elif Agent.MarketData == role:
            return "📈"
        elif Agent.Retrieve == role:
            return "🔍"
        elif Agent.Portfolio == role:
            return "💰"
        else:
            return role
