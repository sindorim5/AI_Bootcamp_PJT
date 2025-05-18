import streamlit as st
import logging
import uuid
from langfuse.callback import CallbackHandler
from common.constants import Mode
from common.utils import dict_to_str
from view.main_view import render_ui, render_portfolio, render_history_view
from database.repository.user_repository import user_repository
from database.repository.session_repository import session_repository
from workflow.state import AgentState
from workflow.graph import create_graph
from workflow.state import ChatState, AgentState

logger = logging.getLogger(__name__)


class MainController:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MainController, cls).__new__(cls)
        return cls._instance

    def start_app(self):
        render_ui()
        self._handle_mode_actions()


    def _handle_mode_actions(self):
        mode = st.session_state.get("app_mode", Mode.Application)

        if mode == Mode.Application:
            pass
        elif mode == Mode.Portfolio:
            chat_graph = self.start_agent()

            langfuse_session_id = str(uuid.uuid4())
            st.session_state["langfuse_session_id"] = langfuse_session_id
            langfuse_handler = CallbackHandler(session_id=langfuse_session_id)

            chat_state: ChatState = {
                "topic" : st.session_state["topic"],
                "user_name" : st.session_state["user_name"],
                "capital" : st.session_state["capital"],
                "risk_level" : st.session_state["risk_level"],
            }

            initial_state: AgentState = {
                "chat_state": chat_state,
                "agent_id": 0,
                "market_data_docs": [],
                "market_data_response": "",
                "retrieve_docs": [],
                "retrieve_response": "",
                "analysis_response": "",
                "portfolio_response": "",
                "context": "",
                "messages": [],
                "response": ""
            }

            stream_gen = chat_graph.stream(
                    initial_state,
                    config={"callbacks": [langfuse_handler]},
                    subgraphs=True,
                    stream_mode="updates",
                )
            render_portfolio(stream_gen)

        elif mode == Mode.History:
            render_history_view()

    def start_agent(self):

        rag = st.session_state['enable_rag']
        chat_graph = create_graph(rag=rag)

        return chat_graph

mainController = MainController()
