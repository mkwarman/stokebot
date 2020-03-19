import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Item(Base):
    __tablename__ = 'item'
    id = Column(Integer, primary_key=True)
    name = Column(String(250))
    username = Column(String(80))
    date_time_added = Column(DateTime, default=datetime.datetime.utcnow)


engine = create_engine("sqlite:///data/held_items.db")

Base.metadata.create_all(engine)
