import os
import logging
import streamlit as st
from sqlalchemy import create_engine
from contextlib import contextmanager
from dotenv import load_dotenv
from database.model import Base
from database.seed import seed

load_dotenv()

logger = logging.getLogger(__name__)

# DB configuration
DB_PATH = os.getenv("DB_PATH")
DATABASE_URL = f"sqlite:///{DB_PATH}"
DB_TYPE = os.getenv("DB_TYPE")

class DatabaseSession:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseSession, cls).__new__(cls)
        return cls._instance

    def initialize(self):
        logger.info("database initialize start")
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(engine)
        try:
            seed()
        except Exception as e:
            logger.error("Error occurred during seeding initial data", exc_info=True)
            raise e
        logger.info("database initialize end")

    @st.cache_resource
    def get_connection(self):
        return st.connection(DB_TYPE, type="sql", url=DATABASE_URL)

    def get_session(self):
        return self.get_connection().session

    @contextmanager
    def get_db_session(self):
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            logger.error("Error occurred during database operation", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

# Initialize the singleton database session
db_session = DatabaseSession()
