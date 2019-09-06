import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Quote(Base):
    __tablename__ = 'quote'
    id = Column(Integer, primary_key=True)
    quote = Column(String(2000))
    author = Column(String(80))
    date_time_added = Column(DateTime, default=datetime.datetime.utcnow)


engine = create_engine("sqlite:///data/quote.db")

Base.metadata.create_all(engine)
