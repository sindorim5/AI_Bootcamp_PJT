from langgraph.graph import StateGraph, END
from workflow.state import ChatState, AgentType
from common.constants import Agent
from workflow.agent.market_data_agent import MarketDataAgent

def create_graph(rag: bool, langfuse_session_id: str = None) -> StateGraph:
    workflow = StateGraph(ChatState)

    market_data_agent = MarketDataAgent(rag=rag, langfuse_session_id=langfuse_session_id)

    workflow.add_node(Agent.MarketData, market_data_agent)
#     workflow.add_node(Agent.Retrieve, retrieve_agent)
#     workflow.add_node(Agent.Analysis, analysis_agent)
#     workflow.add_node(Agent.Portfolio, portfolio_agent)
#     workflow.add_node(Agent.Summary, summary_agent)

#     workflow.add_edge(Agent.MarketData, Agent.Retrieve)
#     workflow.add_edge(Agent.Retrieve, Agent.Analysis)
#     workflow.add_edge(Agent.Analysis, Agent.Portfolio)
#     workflow.add_edge(Agent.Portfolio, Agent.Summary)

#     workflow.set_entry_point(Agent.MarketData)
#     workflow.add_edge(Agent.Summary, END)

    return workflow.compile()


if __name__ == "__main__":

    graph = create_graph()

    graph_image = graph.get_graph().draw_mermaid_png()

    output_path = "chat_graph.png"
    with open(output_path, "wb") as f:
        f.write(graph_image)

    import subprocess

    subprocess.run(["open", output_path])
