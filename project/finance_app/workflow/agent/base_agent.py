from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_core.messages import BaseMessage
from langchain.schema import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langfuse.callback import CallbackHandler
from common.config import get_llm
from common.constants import Agent
from workflow.state import AgentState, ChatState
import streamlit as st
import logging

# Plan-and-execute related imports (kept local to avoid broad impact)
from pydantic import BaseModel, Field
from typing import Union
from langchain_core.prompts import ChatPromptTemplate


logger = logging.getLogger(__name__)

class _PlanModel(BaseModel):
    steps: List[str] = Field(description="Ordered steps to follow")


class _ResponseModel(BaseModel):
    response: str


class _ActModel(BaseModel):
    action: Union[_ResponseModel, _PlanModel] = Field(
        description=(
            "Action to perform. If you want to respond to user, use Response. "
            "If you need to further think or act, use Plan."
        )
    )


class BaseAgent(ABC):
    def __init__(self, system_prompt: str, rag: bool, langfuse_session_id: str = None, plan_enabled: bool = False):
        self.system_prompt = system_prompt
        self.rag = rag
        self._setup_graph()
        self.langfuse_session_id = langfuse_session_id
        self.plan_enabled = plan_enabled

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

        # If planning is in progress, add the current plan context and step instruction
        current_step = state.get("current_step")
        plan = state.get("plan")
        if current_step and plan:
            plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
            step_directive = (
                f"\n\n[Plan Context]\n{plan_str}\n\n"
                f"You are now executing the current step: {current_step}.\n"
                f"Focus strictly on this step using only the provided context."
            )
            prompt = f"{prompt}{step_directive}"

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

    # --------------------
    # Plan & Execute logic
    # --------------------
    def _build_planner(self):
        planner_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "For the given objective, create a concise step-by-step plan. "
                "Only include necessary steps to reach the final answer."
            ),
            ("placeholder", "{messages}"),
        ])
        # Use shared LLM to minimize configuration changes
        return planner_prompt | get_llm().with_structured_output(_PlanModel)

    def _build_replanner(self):
        replanner_prompt = ChatPromptTemplate.from_template(
            """
For the given objective, update the plan based on progress so far.
Only include steps that still need to be done. If you can respond to the user now, return a Response.

Objective:
{input}

Current remaining plan:
{plan}

Completed steps (step, result):
{past_steps}
"""
        )
        return replanner_prompt | get_llm().with_structured_output(_ActModel)

    def _build_objective(self, state: AgentState) -> str:
        chat = state.get("chat_state", {})
        topic = chat.get("topic", "")
        capital = chat.get("capital", "")
        risk = chat.get("risk_level", "")
        # Keep objective concise; system prompt already encodes role-specific rules
        return (
            f"User topic: '{topic}', capital: {capital}, risk level: {risk}. "
            f"As the {self.__class__.__name__}, follow your rules to produce your output."
        )

    def _execute_step(self, state: AgentState, current_step: str, remaining_plan: List[str]) -> AgentState:
        # Invoke the existing graph with additional planning context
        langfuse_handler = CallbackHandler(session_id=self.langfuse_session_id)
        step_state = {**state, "current_step": current_step, "plan": [current_step] + remaining_plan}
        return self.graph.invoke(step_state, config={"callbacks": [langfuse_handler]})

    def run(self, state: AgentState) -> AgentState:
        if not getattr(self, "plan_enabled", False):
            langfuse_handler = CallbackHandler(session_id=self.langfuse_session_id)
            result = self.graph.invoke(state, config={"callbacks":[langfuse_handler]})
            return result

        # Plan-and-execute mode
        planner = self._build_planner()
        replanner = self._build_replanner()
        objective = self._build_objective(state)

        # Initial plan
        plan_obj = planner.invoke({"messages": [("user", objective)]})
        plan: List[str] = plan_obj.steps if plan_obj and plan_obj.steps else []

        working_state: AgentState = {**state}
        past_steps: List[tuple] = []

        # Safety to avoid infinite loops
        max_iters = 20
        iters = 0

        while iters < max_iters:
            iters += 1

            if not plan:
                # If no plan left, ask replanner whether to respond now
                act = replanner.invoke({
                    "input": objective,
                    "plan": plan,
                    "past_steps": past_steps,
                })
                if isinstance(act.action, _ResponseModel):
                    final_text = act.action.response
                    # Update response fields coherently with existing behavior
                    updates: Dict[str, Any] = {"response": final_text}
                    if working_state.get("agent_id") == 1:
                        updates["market_data_response"] = final_text
                    elif working_state.get("agent_id") == 2:
                        updates["retrieve_response"] = final_text
                    elif working_state.get("agent_id") == 3:
                        updates["analysis_response"] = final_text
                    elif working_state.get("agent_id") == 4:
                        updates["portfolio_response"] = final_text
                    return {**working_state, **updates}
                else:
                    plan = act.action.steps or []
                    if not plan:
                        break

            # Execute first remaining step
            current_step = plan[0]
            remaining_plan = plan[1:]
            result = self._execute_step(working_state, current_step, remaining_plan)

            # Record progress and continue
            past_steps.append((current_step, result.get("response", "")))
            working_state = result
            plan = remaining_plan

            # Replan after each step
            act = replanner.invoke({
                "input": objective,
                "plan": plan,
                "past_steps": past_steps,
            })
            if isinstance(act.action, _ResponseModel):
                final_text = act.action.response
                updates: Dict[str, Any] = {"response": final_text}
                if working_state.get("agent_id") == 1:
                    updates["market_data_response"] = final_text
                elif working_state.get("agent_id") == 2:
                    updates["retrieve_response"] = final_text
                elif working_state.get("agent_id") == 3:
                    updates["analysis_response"] = final_text
                elif working_state.get("agent_id") == 4:
                    updates["portfolio_response"] = final_text
                return {**working_state, **updates}
            else:
                plan = act.action.steps or plan

        # Fallback: return last state if loop exits
        return working_state
