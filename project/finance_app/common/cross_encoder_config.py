"""
크로스 인코더 관련 설정을 관리하는 모듈
"""
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# 크로스 인코더 모델 설정
CROSS_ENCODER_MODELS = {
    "default": "cross-encoder/ms-marco-MiniLM-L-6-v2",
    "multilingual": "cross-encoder/ms-marco-MiniLM-L-12-v2",
    "fast": "cross-encoder/ms-marco-MiniLM-L-4-v2",
    "accurate": "cross-encoder/ms-marco-MiniLM-L-12-v2"
}

# 기본 설정값
DEFAULT_CROSS_ENCODER_CONFIG = {
    "model_name": CROSS_ENCODER_MODELS["default"],
    "relevance_threshold": 0.8,
    "max_documents": 15,
    "rerank_top_k": 5,
    "use_cross_encoder": True,
    "cache_models": True
}

def _validate_model_name(model_name: str) -> str:
    """모델명이 유효한지 검증하고 기본값을 반환합니다."""
    if model_name in CROSS_ENCODER_MODELS.values():
        return model_name
    elif model_name in CROSS_ENCODER_MODELS:
        return CROSS_ENCODER_MODELS[model_name]
    else:
        logger.warning(f"알 수 없는 모델명: {model_name}, 기본 모델을 사용합니다.")
        return CROSS_ENCODER_MODELS["default"]

def _validate_threshold(threshold: float) -> float:
    """임계값이 유효한 범위인지 검증합니다."""
    if 0.0 <= threshold <= 1.0:
        return threshold
    else:
        logger.warning(f"임계값이 범위를 벗어남: {threshold}, 기본값 0.6을 사용합니다.")
        return 0.6

def _validate_positive_int(value: int, default: int, name: str) -> int:
    """양의 정수값을 검증합니다."""
    if value > 0:
        return value
    else:
        logger.warning(f"{name}이 유효하지 않음: {value}, 기본값 {default}을 사용합니다.")
        return default

def get_cross_encoder_config() -> Dict[str, Any]:
    """
    환경변수에서 크로스 인코더 설정을 읽어옵니다.
    """
    config = DEFAULT_CROSS_ENCODER_CONFIG.copy()

    # 환경변수에서 설정 읽기
    if os.getenv("CROSS_ENCODER_MODEL"):
        config["model_name"] = _validate_model_name(os.getenv("CROSS_ENCODER_MODEL"))

    if os.getenv("CROSS_ENCODER_THRESHOLD"):
        try:
            threshold = float(os.getenv("CROSS_ENCODER_THRESHOLD"))
            config["relevance_threshold"] = _validate_threshold(threshold)
        except ValueError:
            logger.warning("CROSS_ENCODER_THRESHOLD 값이 숫자가 아닙니다. 기본값을 사용합니다.")

    if os.getenv("CROSS_ENCODER_MAX_DOCS"):
        try:
            max_docs = int(os.getenv("CROSS_ENCODER_MAX_DOCS"))
            config["max_documents"] = _validate_positive_int(max_docs, 15, "최대 문서 수")
        except ValueError:
            logger.warning("CROSS_ENCODER_MAX_DOCS 값이 정수가 아닙니다. 기본값을 사용합니다.")

    if os.getenv("CROSS_ENCODER_TOP_K"):
        try:
            top_k = int(os.getenv("CROSS_ENCODER_TOP_K"))
            config["rerank_top_k"] = _validate_positive_int(top_k, 5, "상위 문서 수")
        except ValueError:
            logger.warning("CROSS_ENCODER_TOP_K 값이 정수가 아닙니다. 기본값을 사용합니다.")

    if os.getenv("USE_CROSS_ENCODER"):
        use_ce = os.getenv("USE_CROSS_ENCODER").lower()
        config["use_cross_encoder"] = use_ce in ["true", "1", "yes", "on"]
        logger.info(f"크로스 인코더 사용: {config['use_cross_encoder']}")

    if os.getenv("CACHE_CROSS_ENCODER_MODELS"):
        cache_models = os.getenv("CACHE_CROSS_ENCODER_MODELS").lower()
        config["cache_models"] = cache_models in ["true", "1", "yes", "on"]

    # 설정 로깅
    logger.info(f"크로스 인코더 설정 로드 완료: {config}")
    return config

def get_cross_encoder_model_name() -> str:
    """크로스 인코더 모델명을 반환합니다."""
    return get_cross_encoder_config()["model_name"]

def get_relevance_threshold() -> float:
    """관련성 점수 임계값을 반환합니다."""
    return get_cross_encoder_config()["relevance_threshold"]

def get_max_documents() -> int:
    """최대 문서 수를 반환합니다."""
    return get_cross_encoder_config()["max_documents"]

def get_rerank_top_k() -> int:
    """재순위화할 상위 문서 수를 반환합니다."""
    return get_cross_encoder_config()["rerank_top_k"]

def is_cross_encoder_enabled() -> bool:
    """크로스 인코더 사용 여부를 반환합니다."""
    return get_cross_encoder_config()["use_cross_encoder"]

def should_cache_models() -> bool:
    """모델 캐싱 여부를 반환합니다."""
    return get_cross_encoder_config()["cache_models"]

def get_available_models() -> Dict[str, str]:
    """사용 가능한 모델 목록을 반환합니다."""
    return CROSS_ENCODER_MODELS.copy()

def validate_config() -> bool:
    """현재 설정이 유효한지 검증합니다."""
    try:
        config = get_cross_encoder_config()

        # 필수 설정 검증
        if not config["model_name"]:
            logger.error("모델명이 설정되지 않았습니다.")
            return False

        if not (0.0 <= config["relevance_threshold"] <= 1.0):
            logger.error("임계값이 유효하지 않습니다.")
            return False

        if config["max_documents"] <= 0 or config["rerank_top_k"] <= 0:
            logger.error("문서 수 설정이 유효하지 않습니다.")
            return False

        logger.info("크로스 인코더 설정 검증 완료")
        return True

    except Exception as e:
        logger.error(f"설정 검증 중 오류 발생: {e}")
        return False
