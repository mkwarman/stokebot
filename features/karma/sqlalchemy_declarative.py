from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Karma(Base):
    __tablename__ = 'karma'
    subject = Column(String(128), primary_key=True)
    karma = Column(Integer, nullable=False)

engine = create_engine("sqlite:///karma.db")

Base.metadata.create_all(engine)
