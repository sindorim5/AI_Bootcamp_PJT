from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from utils.common_utils import current_seoul_time

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id    = Column(Integer, primary_key=True, autoincrement=True)
    audit_dtm  = Column(DateTime(timezone=True), default=current_seoul_time, nullable=False)
    name       = Column(String(10), nullable=False)
    capital    = Column(BigInteger, nullable=False)
    risk_level = Column(Integer, nullable=False)

class Agent(Base):
    __tablename__ = 'agents'
    agent_id  = Column(Integer, primary_key=True, autoincrement=True)
    audit_dtm = Column(DateTime(timezone=True), default=current_seoul_time, nullable=False)
    name      = Column(String, nullable=False)

class Session(Base):
    __tablename__ = 'sessions'
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id    = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    audit_dtm  = Column(DateTime(timezone=True), default=current_seoul_time, nullable=False)
    capital    = Column(BigInteger, nullable=False)
    risk_level = Column(Integer, nullable=False)

class SessionDetail(Base):
    __tablename__ = 'session_details'
    session_id    = Column(Integer, ForeignKey('sessions.session_id'), primary_key=True)
    session_seq   = Column(Integer, primary_key=True)
    audit_dtm     = Column(DateTime(timezone=True), default=current_seoul_time, nullable=False)
    user_input    = Column(Text, nullable=True)
    agent_id      = Column(Integer, ForeignKey('agents.agent_id'), nullable=False)
    agent_message = Column(Text, nullable=False)
    docs          = Column(Text, nullable=True)
