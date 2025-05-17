from database.repository.user_repository import user_repository
from database.model import User
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    pass

class UserController:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserController, cls).__new__(cls)
        return cls._instance

    def on_save_btn(self, user_name: str, capital: float, risk_level:int) -> bool:
        logger.debug("UserController on_save_btn: %s / %d / %d", user_name, risk_level, capital)
        try:
            user = user_repository.get_user_by_name(user_name)
            # 검색된 유저가 없으므로 신규 생성
            if user is None:
                if user_repository.create_user(user_name, capital, risk_level):
                    st.session_state.update(
                        {
                            "user_name": user_name,
                            "capital": capital,
                            "risk_level": risk_level,
                        }
                    )
                    return True
            # 검색된 유저가 있으므로 업데이트
            else:
                if user_repository.update_user(user.user_id, capital, risk_level):
                    st.session_state.update(
                        {
                            "user_name": user.name,
                            "capital": capital,
                            "risk_level": risk_level
                        }
                    )
                    return True
        except RepositoryError as re:
            logger.error(f"RepositoryError in on_save_btn: {re}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in on_save_btn: {e}", exc_info=True)
            return False

    def on_load_btn(self, user_name: str) -> bool:
        user = user_repository.get_user_by_name(user_name)
        if user is None:
            return False
        else:
            st.session_state.update(
                    {
                        "user_name": user.name,
                        "capital": user.capital,
                        "risk_level": user.risk_level
                    }
                )
            return user
