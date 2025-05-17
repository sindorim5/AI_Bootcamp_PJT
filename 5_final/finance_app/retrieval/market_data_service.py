import yfinance as yf
from typing import List, Dict
from langchain.schema import Document
from langchain_core.messages import HumanMessage, SystemMessage
from common.config import get_llm
from common.constants import Agent

# 관련된 종목 찾기
def suggest_related_tickers(
    topic: str, capital: float, risk_level: int
) -> List[str]:

    prompt = (
        f"자본금 {capital}만원, 위험성향 {risk_level}인 투자자에게 필요한 "
        "'{topic}'라는 주제와 관련된 대표 종목 5개의 **yfinance ticker**를 알려주세요. "
        "yfinance ticker라는 정확한 포맷으로 반환하고, 각 ticker는 콤마로 구분해주세요. "
        "예시: 005930.KS, NVDA, ^GSPC 처럼 반환하세요. 설명은 절대 하지 마세요."
    )

    messages = [
        SystemMessage(content="당신은 금융 데이터 전문가입니다. 사용자가 궁금해하는 주제에 대해 종목 ticker를 반환하세요."),
        HumanMessage(content=prompt),
    ]

    response = get_llm().invoke(messages)

    # , 로 구분된 ticker 리스트 추출
    suggested_tickers = [t.strip() for t in response.content.split(",")]

    return suggested_tickers

# 종목 시세 가져오기
def fetch_stock_data(tickers: List[str]) -> List[Document]:
    documents = []
    data = yf.download(tickers, period="1mo", interval="1d", progress=False)

    for ticker in tickers:
        if ticker not in data["Close"].columns:
            continue

        close = data["Close"][ticker].iloc[-1]
        open_price = data["Open"][ticker].iloc[-1]
        change = ((close - open_price) / open_price) * 100

        doc = Document(
            page_content=f"{ticker} 종목 현재가: {close:.2f} USD, 변동률: {change:+.2f}%",
            metadata={
                "ticker": ticker,
                "section": "stock",
                "price": close,
                "change": f"{change:+.2f}%",
            },
        )
        documents.append(doc)

    return documents

# 주요 지수/금리/환율 데이터 가져오기
def fetch_macro_data() -> List[Document]:
    macro_tickers = {
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "KOSPI": "^KS11",
        "KOSDAQ": "^KQ11",
        "USD/KRW": "USDKRW=X",
        "10Y Treasury": "^TNX",
        "WTI 원유": "CL=F",
    }

    data = yf.download(list(macro_tickers.values()), period="1d", interval="1d", progress=False)

    documents = []
    for name, ticker in macro_tickers.items():
        if ticker not in data["Close"].columns:
            continue

        close = data["Close"][ticker].iloc[-1]
        open_price = data["Open"][ticker].iloc[-1]
        change = ((close - open_price) / open_price) * 100

        doc = Document(
            page_content=f"{name} 현재가: {close:.2f}, 변동률: {change:+.2f}%",
            metadata={
                "indicator": name,
                "section": "macro",
                "price": close,
                "change": f"{change:+.2f}%",
            },
        )
        documents.append(doc)

    return documents

# 전체 MarketData Agent
def get_market_data(tickers: List[str]) -> List[Document]:
    stock_docs = fetch_stock_data(tickers)
    macro_docs = fetch_macro_data()
    return stock_docs + macro_docs
