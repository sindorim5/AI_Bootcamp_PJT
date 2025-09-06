import streamlit as st
from typing import List, Dict, Any, Tuple
from langchain.schema import Document
from sentence_transformers import CrossEncoder
from common.cross_encoder_config import get_cross_encoder_config, validate_config
import logging
import numpy as np
import os

logger = logging.getLogger(__name__)

class CrossEncoderService:
    def __init__(self, model_name: str = None):
        """
        크로스 인코더 서비스를 초기화합니다.

        Args:
            model_name: 사용할 크로스 인코더 모델명 (None이면 설정에서 가져옴)
        """
        # 설정 검증
        if not validate_config():
            logger.warning("크로스 인코더 설정이 유효하지 않습니다. 기본값을 사용합니다.")

        self.config = get_cross_encoder_config()
        self.model_name = model_name or self.config["model_name"]
        self.cross_encoder = None
        self._load_model()

    def _load_model(self):
        """크로스 인코더 모델을 로드합니다."""
        try:
            # 크로스 인코더가 비활성화된 경우
            if not self.config["use_cross_encoder"]:
                logger.info("크로스 인코더가 비활성화되었습니다.")
                self.cross_encoder = None
                return

            # 모델 캐싱 설정
            cache_dir = None
            if self.config["cache_models"]:
                cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "cross_encoder")
                os.makedirs(cache_dir, exist_ok=True)
                logger.debug(f"모델 캐시 디렉토리: {cache_dir}")

            logger.info(f"크로스 인코더 모델 로드 시작: {self.model_name}")
            self.cross_encoder = CrossEncoder(
                self.model_name,
                cache_folder=cache_dir
            )
            logger.info(f"CrossEncoder 모델 로드 완료: {self.model_name}")

        except Exception as e:
            logger.error(f"CrossEncoder 모델 로드 실패: {e}")
            logger.warning("크로스 인코더 없이 기본 검색을 사용합니다.")
            self.cross_encoder = None

    def is_available(self) -> bool:
        """크로스 인코더가 사용 가능한지 확인합니다."""
        return (self.cross_encoder is not None and
                self.config["use_cross_encoder"])

    def reload_config(self):
        """설정을 다시 로드합니다."""
        logger.info("크로스 인코더 설정을 다시 로드합니다.")
        self.config = get_cross_encoder_config()
        self._load_model()

    def rerank_documents(
        self,
        query: str,
        documents: List[Document],
        top_k: int = None,
        threshold: float = None
    ) -> List[Tuple[Document, float]]:
        """
        크로스 인코더를 사용하여 문서를 재순위화합니다.

        Args:
            query: 사용자 쿼리
            documents: 재순위화할 문서 리스트
            top_k: 반환할 상위 문서 수 (None이면 설정에서 가져옴)
            threshold: 최소 관련성 점수 임계값 (None이면 설정에서 가져옴)

        Returns:
            재순위화된 (문서, 점수) 튜플 리스트
        """
        if not self.is_available() or not documents:
            logger.debug("크로스 인코더를 사용할 수 없거나 문서가 없습니다.")
            return [(doc, 1.0) for doc in documents[:top_k or self.config["rerank_top_k"]]]

        top_k = top_k or self.config["rerank_top_k"]
        threshold = threshold or self.config["relevance_threshold"]

        try:
            # 쿼리-문서 쌍 생성
            pairs = [(query, doc.page_content) for doc in documents]
            logger.debug(f"문서 재순위화 시작: {len(documents)}개 문서, 임계값: {threshold}")

            # 크로스 인코더로 점수 계산
            scores = self.cross_encoder.predict(pairs)

            # 문서와 점수를 튜플로 묶고 점수로 정렬
            doc_scores = list(zip(documents, scores))
            doc_scores.sort(key=lambda x: x[1], reverse=True)

            # 임계값 이상의 결과만 필터링
            filtered_results = [(doc, score) for doc, score in doc_scores if score >= threshold]

            # top_k만큼 반환
            final_results = filtered_results[:top_k]

            if not final_results:
                logger.warning(f"임계값 {threshold} 이상의 관련 문서가 없습니다.")
            else:
                logger.info(f"문서 재순위화 완료: {len(documents)} -> {len(filtered_results)} -> {len(final_results)}")

            return final_results

        except Exception as e:
            logger.error(f"문서 재순위화 중 오류 발생: {e}")
            return [(doc, 1.0) for doc in documents[:top_k]]

    def filter_by_relevance(
        self,
        query: str,
        documents: List[Document],
        threshold: float = None
    ) -> List[Document]:
        """
        관련성 점수가 임계값 이상인 문서만 필터링합니다.

        Args:
            query: 사용자 쿼리
            documents: 필터링할 문서 리스트
            threshold: 최소 관련성 점수 임계값 (None이면 설정에서 가져옴)

        Returns:
            필터링된 문서 리스트
        """
        if not self.is_available() or not documents:
            return documents

        threshold = threshold or self.config["relevance_threshold"]

        try:
            # 쿼리-문서 쌍 생성
            pairs = [(query, doc.page_content) for doc in documents]
            logger.debug(f"문서 필터링 시작: {len(documents)}개 문서, 임계값: {threshold}")

            # 크로스 인코더로 점수 계산
            scores = self.cross_encoder.predict(pairs)

            # 임계값 이상의 문서만 반환
            filtered_docs = []
            for doc, score in zip(documents, scores):
                if score >= threshold:
                    filtered_docs.append(doc)
                    logger.debug(f"문서 관련성 점수: {score:.3f} - {doc.metadata.get('source', 'Unknown')}")

            if not filtered_docs:
                logger.warning(f"임계값 {threshold} 이상의 관련 문서가 없습니다.")
            else:
                logger.info(f"문서 필터링 완료: {len(documents)} -> {len(filtered_docs)} (임계값: {threshold})")

            return filtered_docs

        except Exception as e:
            logger.error(f"문서 필터링 중 오류 발생: {e}")
            return documents

    def get_relevance_score(self, query: str, document: Document) -> float:
        """
        단일 문서의 관련성 점수를 계산합니다.

        Args:
            query: 사용자 쿼리
            document: 점수를 계산할 문서

        Returns:
            관련성 점수 (0.0 ~ 1.0)
        """
        if not self.is_available():
            return 1.0

        try:
            pair = [(query, document.page_content)]
            score = self.cross_encoder.predict(pair)[0]
            return float(score)
        except Exception as e:
            logger.error(f"관련성 점수 계산 중 오류 발생: {e}")
            return 1.0

    def batch_score_documents(
        self,
        query: str,
        documents: List[Document]
    ) -> List[Tuple[Document, float]]:
        """
        여러 문서의 관련성 점수를 일괄 계산합니다.

        Args:
            query: 사용자 쿼리
            documents: 점수를 계산할 문서 리스트

        Returns:
            (문서, 점수) 튜플 리스트
        """
        if not self.is_available() or not documents:
            return [(doc, 1.0) for doc in documents]

        try:
            # 쿼리-문서 쌍 생성
            pairs = [(query, doc.page_content) for doc in documents]

            # 크로스 인코더로 점수 계산
            scores = self.cross_encoder.predict(pairs)

            # 문서와 점수를 튜플로 묶기
            return list(zip(documents, scores))

        except Exception as e:
            logger.error(f"일괄 점수 계산 중 오류 발생: {e}")
            return [(doc, 1.0) for doc in documents]

    def get_model_info(self) -> Dict[str, Any]:
        """크로스 인코더 모델 정보를 반환합니다."""
        return {
            "model_name": self.model_name,
            "is_available": self.is_available(),
            "config": self.config,
            "model_loaded": self.cross_encoder is not None
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """크로스 인코더 성능 통계를 반환합니다."""
        return {
            "model_name": self.model_name,
            "is_enabled": self.config["use_cross_encoder"],
            "is_loaded": self.cross_encoder is not None,
            "threshold": self.config["relevance_threshold"],
            "max_docs": self.config["max_documents"],
            "top_k": self.config["rerank_top_k"],
            "caching_enabled": self.config["cache_models"]
        }

# 전역 크로스 인코더 서비스 인스턴스
_cross_encoder_service = None

def get_cross_encoder_service() -> CrossEncoderService:
    """전역 크로스 인코더 서비스 인스턴스를 반환합니다."""
    global _cross_encoder_service
    if _cross_encoder_service is None:
        _cross_encoder_service = CrossEncoderService()
    return _cross_encoder_service

def reload_cross_encoder_service():
    """크로스 인코더 서비스를 다시 로드합니다."""
    global _cross_encoder_service
    if _cross_encoder_service:
        _cross_encoder_service.reload_config()
    else:
        _cross_encoder_service = CrossEncoderService()
    return _cross_encoder_service
