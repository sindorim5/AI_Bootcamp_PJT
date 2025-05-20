import streamlit as st
from langchain_community.vectorstores import FAISS
from typing import Any, Dict, Optional, List
from retrieval.retrieve_service import generate_finance_queries, fetch_finance_documents
from common.config import get_embeddings
import logging

logger = logging.getLogger(__name__)

# st.cache_resource 데코레이터를 사용하여 벡터 스토어를 캐싱
def get_topic_vector_store(
    topic: str, capital: float, risk_level: int, language: str = "ko"
) -> Optional[FAISS]:

    # 검색어 개선
    improved_queries = generate_finance_queries(topic, capital, risk_level)
    # 개선된 검색어로 검색 콘텐츠 가져오기
    documents = fetch_finance_documents(improved_queries, language)

    try:
        vector_store = FAISS.from_documents(documents, get_embeddings())
        return vector_store
    except Exception as e:
        logger.error(f"Vector DB 생성 중 오류 발생: {str(e)}")
        return None


def search_topic(topic: str, capital: float, risk_level: int, k: int = 5) -> List[Dict[str, Any]]:
    # 문서를 검색해서 벡터 스토어 생성
    vector_store = get_topic_vector_store(topic, capital, risk_level)
    if not vector_store:
        return []
    try:
        # 벡터 스토어에서 Similarity Search 수행
        return vector_store.similarity_search(topic, k=k)
    except Exception as e:
        st.error(f"검색 중 오류 발생: {str(e)}")
        return []
