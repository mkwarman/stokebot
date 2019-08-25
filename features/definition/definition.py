import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import helpers, featurebase
from definition.dao import get_by_trigger, insert_definition, get_triggers
from definition.sqlalchemy_declarative import Base
from definition.word_check import sanitize_and_split_words

engine = create_engine("sqlite:///data/definition.db")
# Bind the engine to the metadata so we can use the declartives in sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits, rollback, etc

EXPLICIT_RELATION_REGEX = re.compile("&lt;([^@#<>]+)&gt;")

class Definition(featurebase.FeatureBase):
    def on_message(self, text, payload):
        print('got text: ' + text)
        words = sanitize_and_split_words(text)
        print('sanitized and split words:', words)

def get_feature_class():
    return Definition()
