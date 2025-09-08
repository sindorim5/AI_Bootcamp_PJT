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
    try:
        # 입력값 검증
        if not topic or not topic.strip():
            logger.error("주제가 비어있습니다.")
            return []

        if not isinstance(capital, (int, float)) or capital <= 0:
            logger.error(f"잘못된 자본금: {capital}")
            return []

        if not isinstance(risk_level, int) or risk_level < 1 or risk_level > 5:
            logger.error(f"잘못된 위험 수준: {risk_level}")
            return []

        system_prompt = ("""
            "You are an expert financial search query designer. "
            "Your job is to craft concise, high-signal queries that surface reliable and up-to-date "
            "financial market/news data. Adhere strictly to the output rules. Do not add explanations."
        """)

        user_prompt = (
            f"For the topic '{topic}', considering capital {capital} * 10000 (KRW) "
            f"and risk level {risk_level} (1=conservative, 5=aggressive), "
            "propose exactly 3 high-signal web search queries to retrieve timely and reliable "
            "financial news/reports.\n"
            "Constraints:\n"
            "- Each query must be <= 25 characters (including spaces).\n"
            "- Return a single line with 3 queries, comma-separated. Do NOT add any explanation or extra text.\n"
            "- Prefer authoritative sources and recent information (last 90 days) where possible.\n"
            "- Use English keywords; include relevant tickers/indexes when appropriate (e.g., NVDA, ^GSPC, 005930.KS, USDKRW=X).\n"
            "- Exclude low-signal Korean portals/forums using operators. \n"
            "Output format (exactly one line): <query1>, <query2>, <query3>"
        )

        messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        resp = get_llm().invoke(messages).content.strip().split("\n")

        # 응답 처리 및 검증
        queries = []
        for line in resp:
            if line.strip():
                # 쉼표로 분리된 쿼리들
                line_queries = [q.strip() for q in line.split(',') if q.strip()]
                queries.extend(line_queries)

        # 중복 제거 및 길이 제한
        unique_queries = []
        for query in queries:
            if query and len(query) <= 25 and query not in unique_queries:
                unique_queries.append(query)

        # 최대 3개까지만 반환
        final_queries = unique_queries[:3]

        if not final_queries:
            logger.warning("유효한 검색 쿼리를 생성할 수 없습니다. 기본 쿼리를 사용합니다.")
            # 기본 쿼리 제공
            default_queries = [
                f"{topic} investment analysis",
                f"{topic} market news",
                f"{topic} financial report"
            ]
            return default_queries[:3]

        logger.info(f"검색 쿼리 생성 완료: {final_queries}")
        return final_queries

    except Exception as e:
        logger.error(f"검색 쿼리 생성 중 오류 발생: {e}")
        # 에러 발생 시 기본 쿼리 반환
        default_queries = [
            f"{topic} investment analysis",
            f"{topic} market news",
            f"{topic} financial report"
        ]
        return default_queries[:3]


def fetch_finance_documents(
    queries: List[str],
    region: str = "ko",
    max_results: int = 5,
) -> List[Document]:

    if not queries:
        logger.warning("검색 쿼리가 비어있습니다.")
        return []

    ddgs = DDGS()
    documents: List[Document] = []

    for i, query in enumerate(queries):
        try:
            logger.debug(f"쿼리 {i+1} 검색 중: {query}")
            results = ddgs.text(query, region=region, safesearch="moderate", timelimit="y", max_results=max_results) or []

            if not results:
                logger.warning(f"쿼리 '{query}'에 대한 검색 결과가 없습니다.")
                continue

            for j, item in enumerate(results):
                try:
                    title = item.get("title", "")
                    body = item.get("body", "")
                    url = item.get("href", "")

                    # 문서 내용 유효성 검사
                    if not body or len(body.strip()) < 10:  # 최소 10자 이상
                        logger.debug(f"쿼리 '{query}' 결과 {j+1}: 내용이 너무 짧습니다.")
                        continue

                    if not title or len(title.strip()) < 3:  # 제목 최소 3자 이상
                        title = f"검색 결과 {j+1}"

                    # Document 객체 생성
                    doc = Document(
                        page_content=body.strip(),
                        metadata={
                            "source": url or "unknown",
                            "section": "content",
                            "topic": title.strip(),
                            "query": query,
                            "result_index": j + 1
                        }
                    )

                    documents.append(doc)
                    logger.debug(f"문서 추가됨: {title[:50]}...")

                except Exception as e:
                    logger.warning(f"쿼리 '{query}' 결과 {j+1} 처리 중 오류: {e}")
                    continue

        except Exception as e:
            logger.error(f"쿼리 '{query}' 검색 중 오류: {e}")
            st.warning(f"검색 중 오류('{query}'): {e}")
            continue

    logger.info(f"총 {len(documents)}개 문서를 검색했습니다.")
    return documents
