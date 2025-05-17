from enum import Enum

class Tab(Enum):
    My = "내 정보"
    New = "새 대화"
    History = "대화 내역"

class Mode(Enum):
    Application = "application" # default
    Portfolio = "portfolio"     # 포트폴리오 생성 요청 시
    History = "history"         # 대화 내역 요청 시

class Agent(Enum):
    Analysis = "analysis"
    MarketData = "market_data"
    Portfolio = "portfolio"
    Retrieve = "retrieve"
