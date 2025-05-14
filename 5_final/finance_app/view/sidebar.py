import streamlit as st
from common import constants
from view import user_tab

def render_sidebar():
    with st.sidebar:

        tab1, tab2, tab3 = st.tabs([constants.Tab.My.value
                                    , constants.Tab.New.value
                                    , constants.Tab.History.value])

        with tab1:
            user_tab.render_user_tab()

        # with tab2:
        #     render_new_tab()

        # with tab3:
        #     render_history_tab()

