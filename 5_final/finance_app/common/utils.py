from datetime import datetime
from zoneinfo import ZoneInfo
import json, re, ast
from typing import Any, Dict
from workflow.state import AgentState
from langchain.schema import Document, BaseMessage, SystemMessage, HumanMessage, AIMessage

_doc_pat = re.compile(r"page_content='(.*?)'\s+metadata=(\{.*\})$")
_msg_pat = re.compile(r"content='(.*?)'")          # 가장 단순한 메시지 패턴

def current_seoul_time():
    return datetime.now(tz=ZoneInfo("Asia/Seoul"))

def parse_dtm(raw):
    ts  = raw.strftime("%Y-%m-%d %H:%M:%S")
    return ts

def dict_to_str(d: Dict[str, Any]) -> str:
    return json.dumps(
        d,
        ensure_ascii=False,  # 한글을 그대로 쓰려면 False
        default=str,         # 직렬화할 수 없는 객체는 str(obj) 로 변환
        indent=None          # 보기 좋은 들여쓰기
    )

def _parse_doc(doc_str: str) -> Document:
    m = _doc_pat.match(doc_str)
    if not m:
        raise ValueError(f"문서를 파싱할 수 없습니다: {doc_str[:80]}...")
    page_content = m.group(1)
    metadata = ast.literal_eval(m.group(2))
    return Document(page_content=page_content, metadata=metadata)

def _parse_msg(msg_str: str) -> BaseMessage:
    # role 정보를 명시적으로 저장했다면 여기서 분기
    m = _msg_pat.search(msg_str)
    content = m.group(1) if m else msg_str
    return HumanMessage(content=content)

def str_to_agentState(json_str: str) -> AgentState:
    data = json.loads(json_str)

    return AgentState(
        chat_state           = data["chat_state"],
        agent_id             = data["agent_id"],
        market_data_docs     = [_parse_doc(s) for s in data.get("market_data_docs", [])],
        market_data_response = data.get("market_data_response", ""),
        retrieve_docs        = [_parse_doc(s) for s in data.get("retrieve_docs", [])],
        retrieve_response    = data.get("retrieve_response", ""),
        analysis_response    = data.get("analysis_response", ""),
        portfolio_response   = data.get("portfolio_response", ""),
        context              = data.get("context", ""),
        messages             = [_parse_msg(s) for s in data.get("messages", [])],
        response             = data.get("response", ""),
    )





