import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import helpers, featurebase
from definition.dao import get_by_trigger, insert_definition, get_triggers
from definition.sqlalchemy_declarative import Base
from definition.word_check import sanitize_and_split_words, find_unknown_words, check_dictionary

engine = create_engine("sqlite:///data/definition.db")
# Bind the engine to the metadata so we can use the declartives in sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits, rollback, etc

EXPLICIT_RELATION_REGEX = re.compile("&lt;([^@#<>]+)&gt;")

def handle_unknown_words(unknown_words, payload):
    #TODO: check dictionary
    for word in unknown_words:
        print('checking dictionary for ' + word)
        found = check_dictionary(word)
        if found:
            #TODO: add to blacklist
            print('definition found')
            return
        #TODO: ask for definition
        print('no definition found')

class Definition(featurebase.FeatureBase):
    def on_message(self, text, payload):
        print('got text: ' + text)
        words = sanitize_and_split_words(text)
        print('sanitized and split words:', words)
        unique_words = set(words)
        print('unique words:', unique_words)

        #TODO: Check for known words/triggers

        #TODO: Check for target user

        unknown_words = find_unknown_words(unique_words)
        print('unknown words:', unknown_words)
        if unknown_words:
            handle_unknown_words(unknown_words, payload)

def get_feature_class():
    return Definition()
