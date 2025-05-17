import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.model import Base, Agent

load_dotenv()

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH")
DATABASE_URL = f"sqlite:///{DB_PATH}"
DB_TYPE = os.getenv("DB_TYPE")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

def seed():
    logger.info("Seeding initial data")

    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        agent_count = db.query(Agent).count()
        if agent_count == 0:
            # Default agent list
            agents = [
                Agent(agent_id = 1, name="MarketData"),
                Agent(agent_id = 2, name="Retriever"),
                Agent(agent_id = 3, name="Analysis"),
                Agent(agent_id = 4, name="Portfolio"),
            ]
            db.add_all(agents)
            db.commit()
            logger.info("Initial data seeded successfully")
        else:
            logger.info("Initial data already exists, skipping seeding")
    except Exception as e:
        logger.error("Error occurred during seeding initial data", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
