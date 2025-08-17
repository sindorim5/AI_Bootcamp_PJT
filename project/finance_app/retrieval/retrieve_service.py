# finance_app/finance_app/retrieval/retrieval_service.py
import streamlit as st
from typing import List
from duckduckgo_search import DDGS
from langchain.schema import Document
from langchain.schema import HumanMessage, SystemMessage
from common.config import get_llm
import logging


logger = logging.getLogger(__name__)

def generate_finance_queries(topic: str, capital: float, risk_level: int) -> List[str]:
    """
    투자자 프로필에 맞춘 금융 검색 키워드 3개를 생성한다.
    """
    system_prompt = ("""
        "You are an expert financial search query designer. "
        "Your job is to craft concise, high-signal queries that surface reliable and up-to-date "
        "financial market/news data. Adhere strictly to the output rules. Do not add explanations."
    """)

    user_prompt = (
        f"For the topic '{topic}', considering capital {capital} (KRW, 만원 unit) "
        f"and risk level {risk_level} (1=conservative, 5=aggressive), "
        "propose exactly 3 high-signal web search queries to retrieve timely and reliable "
        "financial news/reports.\n"
        "Constraints:\n"
        "- Each query must be <= 25 characters (including spaces).\n"
        "- Return a single line with 3 queries, comma-separated. Do NOT add any explanation or extra text.\n"
        "- Prefer authoritative sources and recent information (last 90 days) where possible.\n"
        "- Use English keywords; include relevant tickers/indexes when appropriate (e.g., NVDA, ^GSPC, 005930.KS, USDKRW=X).\n"
        "- Exclude low-signal Korean portals/forums using operators: "
        "-site:blog.naver.com -site:stock.naver.com -site:cafe.naver.com -site:naver.com -site:dcinside.com\n"
        "- Consider helpful operators when relevant: quotes, AND/OR, site:, intitle:, filetype:pdf.\n"
        "Output format (exactly one line): <query1>, <query2>, <query3>"
    )

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    resp = get_llm().invoke(messages).content.strip().split("\n")
    return [kw.strip() for kw in resp if kw.strip()][:3]


def fetch_finance_documents(
    queries: List[str],
    region: str = "ko",
    max_results: int = 5,
) -> List[Document]:

    ddgs = DDGS()
    documents: List[Document] = []
    for query in queries:
        try:
            results = ddgs.text(query, region=region, safesearch="moderate", timelimit="y", max_results=max_results) or []
            for item in results:
                title = item.get("title", "")
                body = item.get("body", "")
                url = item.get("href", "")

                if body:
                    documents.append(
                        Document(
                            page_content=body,
                            metadata={
                                "source": url,
                                "section": "content",
                                "topic": title,
                                "query": query
                            }
                        )
                    )
        except Exception as e:
            st.warning(f"검색 중 오류('{query}'): {e}")
    return documents
