from datetime import datetime
from zoneinfo import ZoneInfo
import json, re, ast
from typing import Any, Dict
from workflow.state import AgentState
from langchain.schema import Document, BaseMessage, SystemMessage, HumanMessage, AIMessage

# Document / Message 역직렬화용 패턴 (repr 문자열 대응 + 개행 허용)
_doc_pat = re.compile(r"page_content='(.*?)'\s+metadata=(\{.*\})$", re.DOTALL)
_msg_pat = re.compile(r"content='(.*?)'", re.DOTALL)  # 가장 단순한 메시지 패턴

def current_seoul_time():
    return datetime.now(tz=ZoneInfo("Asia/Seoul"))

def parse_dtm(raw):
    ts  = raw.strftime("%Y-%m-%d %H:%M:%S")
    return ts

def dict_to_str(d: Dict[str, Any]) -> str:
    """AgentState 딕셔너리를 JSON 문자열로 직렬화 (기존 포맷 유지).

    - 기존 동작을 유지하기 위해 default=str 를 사용합니다.
    - Document/Message 는 repr 문자열로 저장됩니다.
    """
    return json.dumps(
        d,
        ensure_ascii=False,
        default=str,
        indent=None
    )

def _normalize_meta_literals(text: str) -> str:
    """메타데이터 문자열의 비-리터럴 패턴을 파이썬 리터럴로 치환.

    - np.float32(8.3) → 8.3, np.int64(5) → 5
    - numpy 모듈 접두어가 없어도 동작 (float32(…))는 남겨둠
    """
    # float 계열
    float_num = r"([+-]?(?:\d+\.\d*|\d*\.\d+|\d+)(?:[eE][+-]?\d+)?)"
    text = re.sub(rf"np\.float(?:16|32|64)\s*\(\s*{float_num}\s*\)", r"\1", text)
    # int 계열
    text = re.sub(rf"np\.int(?:8|16|32|64)\s*\(\s*([+-]?\d+)\s*\)", r"\1", text)
    return text


def _parse_doc_from_repr(doc_str: str) -> Document:
    """repr 문자열로 저장된 Document를 최대한 관대하게 파싱한다."""
    m = _doc_pat.search(doc_str)
    if not m:
        # 형식이 전혀 맞지 않으면 전체를 page_content로 취급
        return Document(page_content=str(doc_str), metadata={})

    page_content = m.group(1)
    meta_raw = m.group(2)
    # numpy 스칼라 호출 등 비-리터럴을 선치환
    meta_raw = _normalize_meta_literals(meta_raw)

    # 1) 우선 literal_eval 시도 (가장 안전)
    try:
        metadata = ast.literal_eval(meta_raw)
        if isinstance(metadata, dict):
            return Document(page_content=page_content, metadata=metadata)
    except Exception:
        pass

    # 2) JSON 호환으로 최대한 정규화 후 파싱 시도
    try:
        # True/False/None -> 소문자, NaN/Inf -> null
        normalized = meta_raw
        normalized = re.sub(r"\bTrue\b", "true", normalized)
        normalized = re.sub(r"\bFalse\b", "false", normalized)
        normalized = re.sub(r"\bNone\b", "null", normalized)
        normalized = re.sub(r"\bnan\b|\bNaN\b|\bInfinity\b|\b-?inf\b", "null", normalized)

        # 따옴표를 JSON 형태로 교정 (단순 치환; dict 키/문자열에 한정)
        # 위험 최소화를 위해 { ... } 범위 내에서만 처리
        inner = normalized.strip()
        if inner.startswith("{") and inner.endswith("}"):
            # 키와 문자열 값의 홑따옴표를 쌍따옴표로 치환
            # (이스케이프가 포함된 복잡한 경우는 실패할 수 있지만, 마지막에 빈 메타로 폴백)
            inner = inner.replace("'", '"')
        metadata = json.loads(inner)
        if isinstance(metadata, dict):
            return Document(page_content=page_content, metadata=metadata)
    except Exception:
        pass

    # 3) 끝까지 실패하면 메타데이터는 비워서 반환 (크래시 방지)
    return Document(page_content=page_content, metadata={})


def _to_document(obj: Any) -> Document:
    """다양한 입력 형태를 Document로 변환 (신규/구버전 호환)."""
    if isinstance(obj, Document):
        return obj
    if isinstance(obj, dict):
        # 신규 JSON 포맷
        if obj.get("__type__") == "Document":
            return Document(
                page_content=obj.get("page_content", ""),
                metadata=obj.get("metadata", {}) or {}
            )
        # 혹시 직접 dict로 저장된 경우도 수용
        if "page_content" in obj:
            return Document(page_content=obj.get("page_content", ""), metadata=obj.get("metadata", {}) or {})
        # 그 외는 문자열화하여 repr 파서로 시도
        return _parse_doc_from_repr(str(obj))
    # 문자열 repr 구버전
    return _parse_doc_from_repr(str(obj))

def _parse_msg(msg_str: str) -> BaseMessage:
    # 단순 문자열 repr 호환
    m = _msg_pat.search(str(msg_str))
    content = m.group(1) if m else str(msg_str)
    return HumanMessage(content=content)


def _to_message(obj: Any) -> BaseMessage:
    """다양한 입력 형태를 BaseMessage로 변환 (신규/구버전 호환)."""
    if isinstance(obj, BaseMessage):
        return obj
    if isinstance(obj, dict) and obj.get("__type__") == "Message":
        role = obj.get("role", "human")
        content = obj.get("content", "")
        if role == "system":
            return SystemMessage(content=content)
        if role == "ai":
            return AIMessage(content=content)
        return HumanMessage(content=content)
    # 기타 문자열/미상 포맷은 구버전 파서 사용
    return _parse_msg(str(obj))

def str_to_agentState(json_str: str) -> AgentState:
    data = json.loads(json_str)

    return AgentState(
        chat_state           = data["chat_state"],
        agent_id             = data["agent_id"],
        market_data_docs     = [_to_document(s) for s in data.get("market_data_docs", [])],
        market_data_response = data.get("market_data_response", ""),
        retrieve_docs        = [_to_document(s) for s in data.get("retrieve_docs", [])],
        retrieve_response    = data.get("retrieve_response", ""),
        analysis_response    = data.get("analysis_response", ""),
        portfolio_response   = data.get("portfolio_response", ""),
        context              = data.get("context", ""),
        messages             = [_to_message(s) for s in data.get("messages", [])],
        response             = data.get("response", ""),
    )





