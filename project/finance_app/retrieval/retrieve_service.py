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
    """LLM에게 금융 뉴스·리포트 검색어 3개를 제안받습니다."""
    template = (
        f"'{topic}'이라는 질문에 대해 "
        f"자본금 {capital}만원, 위험성향 {risk_level}(1 ~ 5등급, 숫자가 클수록 공격투자형)인 투자자에게 필요한 "
        "시세/시장/뉴스 데이터를 찾기 위한 검색어를 3개 제안해주세요."
        "네이버 블로그나 네이버 증권은 참고하지 말아주세요."
        "각 검색어는 25자 이내로 콤마로 구분하고 설명은 하지 마세요."
    )
    prompt = template.format(topic=topic)

    messages = [
        SystemMessage("당신은 금융 분야 데이터 검색 전문가입니다."),
        HumanMessage(prompt),
    ]
    response = get_llm().invoke(messages)
    return [q.strip() for q in response.content.split(",")][:3]

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
