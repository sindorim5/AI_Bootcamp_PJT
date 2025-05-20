from database.model import Agent
from database.session import db_session
import logging

logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    pass

class AgentRepository:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentRepository, cls).__new__(cls)
        return cls._instance

    def get_agent_by_id(self, agent_id: int) -> Agent | None:
        try:
            with db_session.get_db_session() as session:
                agents = session.query(Agent).filter(Agent.agent_id == agent_id).all()
                if len(agents) == 1:
                    return agents[0]
                elif len(agents) > 1:
                    raise RepositoryError(f"multiple agents with the same id")
                else:
                    return None
        except Exception as e:
            logger.error(f"AgentRepository get_agent_by_id: {str(e)}")
            raise e

    def get_agent_by_name(self, name: str) -> Agent | None:
        try:
            with db_session.get_db_session() as session:
                agents = session.query(Agent).filter(Agent.name == name).all()
                if len(agents) == 1:
                    return agents[0]
                elif len(agents) > 1:
                    raise RepositoryError(f"multiple agents with the same name")
                else:
                    return None
        except Exception as e:
            logger.error(f"AgentRepository get_agent_by_name: {str(e)}")
            raise e

agent_repository = AgentRepository()
