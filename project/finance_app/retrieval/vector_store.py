import streamlit as st
from langchain_community.vectorstores import FAISS
from typing import Any, Dict, Optional, List
from retrieval.retrieve_service import generate_finance_queries, fetch_finance_documents
from retrieval.cross_encoder_service import get_cross_encoder_service
from common.config import get_embeddings
import logging

logger = logging.getLogger(__name__)

# st.cache_resource 데코레이터를 사용하여 벡터 스토어를 캐싱
def get_topic_vector_store(
    topic: str, capital: float, risk_level: int, language: str = "ko"
) -> Optional[FAISS]:

    try:
        # 검색어 개선
        improved_queries = generate_finance_queries(topic, capital, risk_level)
        
        # 검색어가 비어있는 경우 처리
        if not improved_queries:
            logger.warning(f"주제 '{topic}'에 대한 검색어를 생성할 수 없습니다.")
            return None
            
        # 개선된 검색어로 검색 콘텐츠 가져오기
        documents = fetch_finance_documents(improved_queries, language)
        
        # 검색된 문서가 없는 경우 처리
        if not documents:
            logger.warning(f"주제 '{topic}'에 대한 검색 결과가 없습니다.")
            return None
            
        # 문서 유효성 검사
        valid_documents = []
        for i, doc in enumerate(documents):
            try:
                # Document 객체가 유효한지 확인
                if hasattr(doc, 'page_content') and doc.page_content and len(doc.page_content.strip()) > 0:
                    valid_documents.append(doc)
                else:
                    logger.warning(f"문서 {i}의 내용이 비어있습니다.")
            except Exception as e:
                logger.warning(f"문서 {i} 처리 중 오류: {e}")
                continue
        
        if not valid_documents:
            logger.warning(f"주제 '{topic}'에 대한 유효한 문서가 없습니다.")
            return None
            
        logger.info(f"벡터 스토어 생성 시작: {len(valid_documents)}개 유효 문서")
        
        # FAISS 벡터 스토어 생성
        vector_store = FAISS.from_documents(valid_documents, get_embeddings())
        logger.info(f"벡터 스토어 생성 완료: {len(valid_documents)}개 문서")
        return vector_store
        
    except Exception as e:
        logger.error(f"Vector DB 생성 중 오류 발생: {str(e)}")
        logger.error(f"주제: {topic}, 자본금: {capital}, 위험수준: {risk_level}")
        return None


def search_topic(
    topic: str,
    capital: float,
    risk_level: int,
    k: int = 5,
    use_cross_encoder: bool = True,
    relevance_threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    주제에 대한 검색을 수행하고 크로스 인코더로 결과를 재순위화합니다.

    Args:
        topic: 검색 주제
        capital: 자본금
        risk_level: 위험 수준
        k: 반환할 문서 수
        use_cross_encoder: 크로스 인코더 사용 여부
        relevance_threshold: 관련성 점수 임계값
    """
    # 문서를 검색해서 벡터 스토어 생성
    vector_store = get_topic_vector_store(topic, capital, risk_level)
    if not vector_store:
        return []

    try:
        # 벡터 스토어에서 Similarity Search 수행 (더 많은 결과를 가져와서 필터링)
        initial_k = k * 3 if use_cross_encoder else k
        documents = vector_store.similarity_search(topic, k=initial_k)

        if not use_cross_encoder or not documents:
            return documents[:k]

        # 크로스 인코더로 문서 재순위화 및 필터링
        cross_encoder_service = get_cross_encoder_service()

        # 관련성 점수로 문서 필터링
        filtered_docs = cross_encoder_service.filter_by_relevance(
            query=topic,
            documents=documents,
            threshold=relevance_threshold
        )

        # 필터링된 문서를 재순위화
        reranked_docs = cross_encoder_service.rerank_documents(
            query=topic,
            documents=filtered_docs,
            top_k=k
        )

        # 점수 정보를 메타데이터에 추가
        final_docs = []
        for doc, score in reranked_docs:
            # 원본 메타데이터 복사
            metadata = doc.metadata.copy() if hasattr(doc, 'metadata') else {}
            metadata['relevance_score'] = float(score)
            metadata['cross_encoder_used'] = True

            # 새로운 Document 객체 생성
            from langchain.schema import Document
            final_doc = Document(
                page_content=doc.page_content,
                metadata=metadata
            )
            final_docs.append(final_doc)

        logger.info(f"크로스 인코더 적용 완료: {len(documents)} -> {len(filtered_docs)} -> {len(final_docs)}")
        return final_docs

    except Exception as e:
        st.error(f"검색 중 오류 발생: {str(e)}")
        return []


def search_topic_with_scores(
    topic: str,
    capital: float,
    risk_level: int,
    k: int = 5,
    use_cross_encoder: bool = True,
    relevance_threshold: float = 0.6
) -> List[tuple]:
    """
    주제에 대한 검색을 수행하고 크로스 인코더 점수와 함께 결과를 반환합니다.

    Returns:
        (Document, relevance_score) 튜플 리스트
    """
    # 문서를 검색해서 벡터 스토어 생성
    vector_store = get_topic_vector_store(topic, capital, risk_level)
    if not vector_store:
        return []

    try:
        # 벡터 스토어에서 Similarity Search 수행
        initial_k = k * 3 if use_cross_encoder else k
        documents = vector_store.similarity_search(topic, k=initial_k)

        if not use_cross_encoder or not documents:
            return [(doc, 1.0) for doc in documents[:k]]

        # 크로스 인코더로 문서 재순위화 및 필터링
        cross_encoder_service = get_cross_encoder_service()

        # 관련성 점수로 문서 필터링
        filtered_docs = cross_encoder_service.filter_by_relevance(
            query=topic,
            documents=documents,
            threshold=relevance_threshold
        )

        # 필터링된 문서가 없는 경우 처리
        if not filtered_docs:
            logger.warning(f"주제 '{topic}'에 대한 관련성 높은 문서가 없습니다. (임계값: {relevance_threshold})")
            return []

        # 필터링된 문서를 재순위화
        reranked_docs = cross_encoder_service.rerank_documents(
            query=topic,
            documents=filtered_docs,
            top_k=k
        )

        # 재순위화된 문서가 없는 경우 처리
        if not reranked_docs:
            logger.warning(f"주제 '{topic}'에 대한 재순위화된 문서가 없습니다.")
            return []

        return reranked_docs

    except Exception as e:
        st.error(f"검색 중 오류 발생: {str(e)}")
        return []
