import os
import getpass
import operator
import asyncio
from typing import Annotated, List, Tuple, Union

from dotenv import load_dotenv
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

# =========================================
# 1. 환경 변수 로드
# =========================================
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

load_dotenv()
_set_env("OPENAI_API_KEY")
_set_env("TAVILY_API_KEY")
_set_env("MODEL")

# =========================================
# 2. 툴 & 에이전트 정의
# =========================================
tools = [TavilySearchResults(max_results=3)]
llm = ChatOpenAI(model=os.getenv("MODEL"))
prompt = "You are a helpful assistant."
agent_executor = create_react_agent(llm, tools, prompt=prompt)

# =========================================
# 3. 상태 정의
# =========================================
class PlanExecute(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str

# =========================================
# 4. 플래너 & 리플래너 모델
# =========================================
class Plan(BaseModel):
    """Plan to follow in future"""
    steps: List[str] = Field(description="different steps to follow, should be in sorted order")

planner_prompt = ChatPromptTemplate.from_messages([
    ("system", """For the given objective, come up with a simple step by step plan.
This plan should involve individual tasks, that if executed correctly will yield the correct answer.
Do not add any superfluous steps. The result of the final step should be the final answer.
Make sure that each step has all the information needed - do not skip steps."""),
    ("placeholder", "{messages}"),
])
planner = planner_prompt | ChatOpenAI(model=os.getenv("MODEL"), temperature=0).with_structured_output(Plan)

# 리플래너 모델
class Response(BaseModel):
    """Response to user."""
    response: str

class Act(BaseModel):
    """Action to perform."""
    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
                    "If you need to further use tools to get the answer, use Plan."
    )

replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan.
This plan should involve individual tasks, that if executed correctly will yield the correct answer.
Do not add any superfluous steps. The result of the final step should be the final answer.
Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the follow steps:
{past_steps}

Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that.
Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done.
Do not return previously done steps as part of the plan."""
)
replanner = replanner_prompt | ChatOpenAI(model=os.getenv("MODEL"), temperature=0).with_structured_output(Act)

# =========================================
# 5. 그래프 노드 정의
# =========================================
async def plan_step(state: PlanExecute):
    plan = await planner.ainvoke({"messages": [("user", state["input"])]})
    return {"plan": plan.steps}

async def execute_step(state: PlanExecute):
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"For the following plan:\n{plan_str}\n\nYou are tasked with executing step 1, {task}."
    agent_response = await agent_executor.ainvoke({"messages": [("user", task_formatted)]})
    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
        # 실행한 스텝 제거
        "plan": plan[1:]
    }

async def replan_step(state: PlanExecute):
    output = await replanner.ainvoke(state)
    if isinstance(output.action, Response):
        return {"response": output.action.response}
    else:
        return {"plan": output.action.steps}

def should_end(state: PlanExecute):
    if state.get("response"):
        return END
    else:
        return "agent"

# =========================================
# 6. 그래프 구성
# =========================================
workflow = StateGraph(PlanExecute)
workflow.add_node("planner", plan_step)
workflow.add_node("agent", execute_step)
workflow.add_node("replan", replan_step)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "agent")
workflow.add_edge("agent", "replan")
workflow.add_conditional_edges("replan", should_end, ["agent", END])

app = workflow.compile()

# =========================================
# 7. 시각화 & 실행
# =========================================
display(Image(app.get_graph(xray=True).draw_mermaid_png()))

config = {"recursion_limit": 20}
inputs = {"input": "what is the hometown of the 2025 F1 Austrian Grand Prix winner?"}

async def run():
    async for event in app.astream(inputs, config):
        for k, v in event.items():
            if k != "__end__":
                print("=" * 60)
                print(v)

asyncio.run(run())
