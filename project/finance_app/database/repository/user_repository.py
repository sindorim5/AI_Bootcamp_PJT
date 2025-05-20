from database.model import User
from database.session import db_session
import logging

logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    pass

class UserRepository:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserRepository, cls).__new__(cls)
        return cls._instance

    def get_user_by_id(self, user_id: int) -> User | None:
        try:
            with db_session.get_db_session() as session:
                users = session.query(User).filter(User.user_id == user_id).all()
                if len(users) == 1:
                    return users[0]
                elif len(users) > 1:
                    raise RepositoryError(f"multiple users with the same id")
                else:
                    return None
        except Exception as e:
            logger.error(f"UserRepository get_user_by_id: {str(e)}")
            raise e

    def get_user_by_name(self, user_name: str) -> User | None:
        try:
            with db_session.get_db_session() as session:
                users = session.query(User).filter(User.name == user_name).all()
                if len(users) == 1:
                    return users[0]
                elif len(users) > 1:
                    raise RepositoryError(f"multiple users with the same name")
                else:
                    return None
        except Exception as e:
            logger.error(f"UserRepository get_user_by_name: {str(e)}")
            raise e

    def create_user(self, name: str, capital: float, risk_level: int) -> bool:
        try:
            with db_session.get_db_session() as session:
                temp_user = User(name=name, capital=capital, risk_level=risk_level)
                session.add(temp_user)
                return True
        except RepositoryError as e:
            logger.error(f"UserRepository create_user: {str(e)}")
            raise e
        except Exception as e:
            logger.error(f"UserRepository create_user: {str(e)}")
            raise e

    def update_user(self, user_id: int, capital: float, risk_level: int) -> bool:
        try:
            with db_session.get_db_session() as session:
                updated = (
                    session
                    .query(User)
                    .filter(User.user_id == user_id)
                    .update({
                        "capital": capital,
                        "risk_level": risk_level
                    })
                )
                return updated == 1
        except RepositoryError as e:
            logger.error(f"UserRepository create_user: {str(e)}")
            raise e
        except Exception as e :
            logger.error(f"UserRepository update_user: {str(e)}")
            raise e


user_repository = UserRepository()
