import os
import logging
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.model import Base
from database.seed import seed

# ENV, LOGGING
load_dotenv()
logger = logging.getLogger(__name__)
DB_PATH      = os.getenv("DB_PATH", "./finance_agent.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ENGINE, SESSION
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


class DatabaseSession:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self) -> None:
        logger.info("Database initialize start")
        Base.metadata.create_all(engine)
        try:
            seed()
        except Exception:
            logger.exception("Seeding initial data failed")
            raise
        logger.info("Database initialize end")

    def get_session(self):
        return SessionLocal()

    @contextmanager
    def get_db_session(self):
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            logger.exception("Error during DB operation")
            session.rollback()
            raise
        finally:
            session.close()


# module‐level singleton
db_session = DatabaseSession()
