from abc import ABC, abstractmethod
from typing import List, Dict, Any, TypedDict
from langchain_core.messages import BaseMessage
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langfuse.callback import CallbackHandler
from common.config import get_llm
from common.constants import Agent
from workflow.state import AgentState, ChatState
import streamlit as st
import logging


logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    def __init__(self, system_prompt: str, rag: bool, langfuse_session_id: str = None):
        self.system_prompt = system_prompt
        self.rag = rag
        self._setup_graph()
        self.langfuse_session_id = langfuse_session_id

    def _setup_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("prepare_messages", self._prepare_messages)
        workflow.add_node("generate_response", self._generate_response)

        workflow.add_edge("retrieve_context", "prepare_messages")
        workflow.add_edge("prepare_messages", "generate_response")
        workflow.add_edge("generate_response", END)

        workflow.set_entry_point("retrieve_context")
        self.graph = workflow.compile()

    @abstractmethod
    def _retrieve_context(self, state: AgentState) -> AgentState:
        pass

    @abstractmethod
    def _create_prompt(self, state: AgentState) -> str:
        pass

    # 검색 결과로 Context 생성
    def _format_context(self, docs) -> str:
        # 문자열을 그대로 받으면 바로 반환
        if isinstance(docs, str):
            return docs

        context = ""
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown")
            section = doc.metadata.get("section", "")
            context += f"[문서 {i + 1}] 출처: {source}"
            if section:
                context += f", 섹션: {section}"
            context += f"\n{doc.page_content}\n\n"
        return context

    def _prepare_messages(self, state: AgentState) -> AgentState:

        messages = [SystemMessage(content=self.system_prompt)]
        prompt = self._create_prompt(state)
        messages.append(HumanMessage(content=prompt))

        return {**state, "messages": messages}

    def _generate_response(self, state: AgentState) -> AgentState:
        messages = state["messages"]
        response = get_llm().invoke(messages)

        updates: Dict[str, Any] = {
            "response": response.content
        }

        if state["agent_id"] == 1:
            updates["market_data_response"] = response.content
        elif state["agent_id"] == 2:
            updates["retrieve_response"] = response.content
        elif state["agent_id"] == 3:
            updates["analysis_response"] = response.content
        elif state["agent_id"] == 4:
            updates["portfolio_response"] = response.content

        return {**state, **updates}

    def run(self, state: AgentState) -> AgentState:
        langfuse_handler = CallbackHandler(session_id=self.langfuse_session_id)
        result = self.graph.invoke(state, config={"callbacks":[langfuse_handler]})
        return result
