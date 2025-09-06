import yfinance as yf
from typing import List, Dict
from langchain.schema import Document
from langchain_core.messages import HumanMessage, SystemMessage
from common.config import get_llm
from common.constants import Agent
import logging


logger = logging.getLogger(__name__)

# 관련된 종목 찾기


def suggest_related_tickers(
    topic: str, capital: float, risk_level: int
) -> List[str]:

    prompt = (
        f"자본금 {capital}만원, 위험성향 {risk_level}(1 ~ 5등급, 숫자가 클수록 공격투자형)인 투자자에게 필요한 "
        f"'{topic}'라는 주제와 관련된 대표 종목 5개의 **yfinance ticker**를 알려주세요. "
        "yfinance ticker라는 정확한 포맷으로 반환하고, 각 ticker는 콤마로 구분해주세요. "
        "예시: 005930.KS, NVDA, ^GSPC 처럼 반환하세요. 설명은 절대 하지 마세요."
    )

    system_prompt = ("""
        Role: You are a "yfinance ticker selector".
        Your job is to select exactly 5 valid yfinance tickers strictly following the rules.

        Forbidden:
        - Any explanation, description, reasoning, or commentary
        - Extra whitespace, line breaks, bullets, or numbering
        - Company names without tickers, ISINs, or other identifiers

        Required:
        - Exactly 5 tickers
        - Output in one single line, separated by commas
        - Must be valid yfinance format(e.g., 005930.KS, NVDA, ^ GSPC, BTC-USD, CL=F)

        Risk rules:
        - Risk level 1–2: Focus on indexes/ETFs(2–3), large-cap defensive stocks(1–2), optional hedge(0–1)
        - Risk level 3: Balanced between indexes/ETFs(2), mega-cap leaders(2), growth/sector theme(1)
        - Risk level 4–5: Growth and sector leaders(3–4), indexes/hedge(1–2)

        Regional suffix hints:
        - Korea KOSPI: .KS, KOSDAQ: .KQ
        - Japan: .T, UK: .L, Hong Kong: .HK, Shanghai: .SS
        - Index: ^ GSPC(S & P 500), ^ IXIC(NASDAQ), ^ KS11(KOSPI)
        - Commodities: CL=F(WTI), GC=F(Gold)
        - FX: USDKRW=X
        - Crypto: BTC-USD, ETH-USD

        Output language:
        - Output tickers only(no explanation).
    """)

    human_prompt = (f"""
        Topic: '{topic}'
        Capital: {capital} (in KRW, 만원 unit)
        Risk level: {risk_level}(1=conservative, 5=aggressive)

        Task:
        Return exactly 5 related yfinance tickers in one line, separated by commas.
        Do not explain.
    """)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    response = get_llm().invoke(messages)

    # , 로 구분된 ticker 리스트 추출
    suggested_tickers = [t.strip() for t in response.content.split(",")]

    return suggested_tickers

# 종목 시세 가져오기
def fetch_stock_data(tickers: List[str]) -> List[Document]:
    documents = []
    data = yf.download(
        tickers,
        period="2mo",
        interval="1d",
        progress=False,
        threads=False,
    )

    for ticker in tickers:
        # 멀티티커 → DataFrame, 단일티커 → Series 형태일 수 있음
        try:
            close_val = data["Close"][ticker].iloc[-1]
            open_val = data["Open"][ticker].iloc[-1]
        except (KeyError, IndexError, TypeError):
            # 컬럼이 없거나 빈 Series 인 경우
            doc = Document(
                page_content=f"{ticker} 종목: 데이터 없음",
                metadata={
                    "ticker": ticker,
                    "section": "stock",
                    "price": None,
                    "change": "없음",
                },
            )
            documents.append(doc)
            continue

        # NaN 검사
        if _is_nan(close_val) or _is_nan(open_val):
            doc = Document(
                page_content=f"{ticker} 종목: 데이터 없음",
                metadata={
                    "ticker": ticker,
                    "section": "stock",
                    "price": None,
                    "change": "없음",
                },
            )
            documents.append(doc)
            continue

        # 정상 데이터라면 변동률 계산
        change_pct = (close_val - open_val) / open_val * 100

        info = yf.Ticker(ticker).info
        name = info.get("shortName") or info.get("longName") or ticker

        doc = Document(
            page_content=f"{ticker} 종목 현재가: {close_val:.2f} USD, 변동률: {change_pct:+.2f}%",
            metadata={
                "ticker": ticker,
                "name": name,
                "section": "stock",
                "price": float(close_val),
                "change": f"{change_pct:+.2f}%",
            },
        )
        documents.append(doc)

    return documents

# 주요 지수/금리/환율 데이터 가져오기
def fetch_macro_data() -> List[Document]:
    macro_tickers: Dict[str, str] = {
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "KOSPI": "^KS11",
        "KOSDAQ": "^KQ11",
        "USD/KRW": "USDKRW=X",
        "10Y Treasury": "^TNX",
        "WTI 원유": "CL=F",
    }

    data = yf.download(
        list(macro_tickers.values()),
        period="2mo",
        interval="1d",
        progress=False,
        threads=False,
        group_by="column"
    )

    # 멀티-인덱스를 티커별 Close / Open 테이블로 변환
    #   * yfinance 0.2.x: ('Price','Close',ticker)
    if data.columns.nlevels == 3:
        close_df = data.xs("Close", level=1, axis=1)
        open_df = data.xs("Open",  level=1, axis=1)
    else:
        close_df = data["Close"]
        open_df = data["Open"]

    documents: List[Document] = []

    for name, ticker in macro_tickers.items():
        # 컬럼 자체가 없으면 스킵
        if ticker not in close_df.columns:
            continue

        # 최근 유효값 추출(dropna 로 NaN 제거)
        close_series = close_df[ticker].dropna()
        open_series = open_df[ticker].dropna()

        if close_series.empty or open_series.empty:
            # 데이터 완전 없음
            doc = Document(
                page_content=f"{name} 데이터 없음",
                metadata={
                    "indicator": name,
                    "section": "macro",
                    "price": None,
                    "change": "없음",
                },
            )
            documents.append(doc)
            continue

        close_val = close_series.iloc[-1]
        open_val = open_series.iloc[-1]

        # NaN 방어(혹시 남아 있을 경우)
        if _is_nan(close_val) or _is_nan(open_val):
            doc = Document(
                page_content=f"{name} 데이터 없음",
                metadata={
                    "indicator": name,
                    "section": "macro",
                    "price": None,
                    "change": "없음",
                },
            )
            documents.append(doc)
            continue

        change_pct = (close_val - open_val) / open_val * 100

        documents.append(
            Document(
                page_content=f"{name} 현재가: {close_val:.2f}, 변동률: {change_pct:+.2f}%",
                metadata={
                    "indicator": name,
                    "section": "macro",
                    "price": float(close_val),
                    "change": f"{change_pct:+.2f}%",
                },
            )
        )

    return documents


def _is_nan(x) -> bool:
    return x != x

# 전체 MarketData Agent
def get_market_data(tickers: List[str]) -> List[Document]:
    stock_docs = fetch_stock_data(tickers)
    macro_docs = fetch_macro_data()
    return stock_docs + macro_docs
