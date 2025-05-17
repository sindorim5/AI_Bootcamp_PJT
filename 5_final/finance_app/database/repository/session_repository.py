from database.model import User, Session
from database.session import db_session
import logging

logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    pass

class SessionRepository:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SessionRepository, cls).__new__(cls)
        return cls._instance

    def get_session_by_id(self, session_id: int) -> list | None:
        try:
            with db_session.get_db_session() as db:
                sessions = db.query(Session).filter(Session.session_id == session_id).all()
                if len(sessions) == 1:
                    return sessions[0]
                elif len(sessions) > 1:
                    raise RepositoryError(f"multiple sessions with the same id")
                else:
                    return None
        except Exception as e:
            logger.error(f"SessionRepository get_session_by_id: {str(e)}")
            raise e

    def get_session_by_user_id(self, user_id: int) -> list | None:
        try:
            with db_session.get_db_session() as db:
                sessions = db_session.query(Session).filter(Session.user_id == user_id).all()
                if len(sessions) > 0:
                    return sessions
                else:
                    return None
        except Exception as e:
            logger.error(f"SessionRepository get_session_by_user_id: {str(e)}")
            raise e

    def create_session(self, user: User, topic: str) -> bool:
        try:
            with db_session.get_db_session() as db:
                temp_session = Session(
                    user_id=user.user_id,
                    capital=user.capital,
                    risk_level=user.risk_level,
                    topic=topic
                    )
                db.add(temp_session)
                db.flush()
                new_session_id = temp_session.session_id
                return new_session_id
        except Exception as e:
            logger.error(f"SessionRepository create_session: {str(e)}")
            raise e

session_repository = SessionRepository()
