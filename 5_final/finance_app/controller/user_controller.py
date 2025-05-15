from database.repository.user_repository import user_repository
from database.model import User
import streamlit as st
import logging

logger = logging.getLogger(__name__)

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
                new_user = User(
                    name=user_name,
                    capital=capital,
                    risk_level=risk_level
                    )
                if user_repository.create_user(new_user):
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
                if user_repository.update_user(user, capital, risk_level):
                    st.session_state.update(
                        {
                            "user_name": user.name,
                            "capital": capital,
                            "risk_level": risk_level
                        }
                    )
                    return True
        except Exception as e:
            logger.error(f"UserController on_save_btn: {str(e)}")
            return False
