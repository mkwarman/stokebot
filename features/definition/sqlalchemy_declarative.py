import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Definition(Base):
    __tablename__ = 'definition'
    id = Column(Integer, primary_key=True)
    trigger = Column(Text)
    relation = Column(Integer)
    response = Column(Text)
    user = Column(String(80))
    date_time_added = Column(DateTime, default=datetime.datetime.utcnow)


class Blacklist(Base):
    __tablename__ = 'blacklist'
    trigger = Column(Text, primary_key=True)
    user = Column(String(80))
    date_time_added = Column(DateTime, default=datetime.datetime.utcnow)


class Ignore(Base):
    __tablename__ = 'ignore'
    ignored_user_id = Column(String(80), primary_key=True)
    date_time_added = Column(DateTime, default=datetime.datetime.utcnow)


class WordUsage(Base):
    __tablename__ = 'word_usage'
    trigger = Column(Text, primary_key=True)
    times_used = Column(Integer)


engine = create_engine("sqlite:///data/definition.db")

Base.metadata.create_all(engine)
