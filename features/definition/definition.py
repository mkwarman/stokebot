import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import helpers, featurebase
from definition.dao import get_by_trigger, insert_definition, get_triggers, check_blacklist, insert_blacklist, check_ignored, insert_ignored, remove_ignored
from definition.sqlalchemy_declarative import Base
from definition.word_check import sanitize_and_split_words, find_unknown_words, check_dictionary

engine = create_engine("sqlite:///data/definition.db")
# Bind the engine to the metadata so we can use the declartives in sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits, rollback, etc

EXPLICIT_RELATION_REGEX = re.compile("&lt;([^@#<>]+)&gt;")

def handle_unknown_words(unknown_words, payload):
    session = DBSession()

    for word in unknown_words:
        # Check for unknown word in blacklist
        found = check_blacklist(session, word)
        if found:
            return
        # Check for unknown word in dictionary
        found = check_dictionary(word)
        if found:
            insert_blacklist(session, word, 'dictionary')
            return
        #TODO: ask for definition
        print('no definition found')

    session.close()

def handle_ignore(ignore, payload):
    user = helpers.get_user_from_payload(payload)

    if not user:
        # If this is not a person
        return

    session = DBSession()
    if ignore:
        insert_ignored(session, user)
    else:
        remove_ignored(session, user)
    #insert_ignored(session, user) if ignore else remove_ignored(session, user)
    session.close()
    #TODO: Update user

def is_ignored_user(payload):
    user = helpers.get_user_from_payload(payload)

    if not user:
        # If this is not a person
        return

    session = DBSession()
    ignored = check_ignored(session, user)
    session.close()

    return True if ignored else False


class Definition(featurebase.FeatureBase):
    def on_message(self, text, payload):
        if is_ignored_user(payload):
            return

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

    def on_command(self, command, payload):
        # convert to lowercase since we dont care about casing for any of these commands
        command = command.lower()
        if command.startswith("ignore me"):
            handle_ignore(True, payload)
            return True
        elif command.startswith("listen to me"):
            handle_ignore(False, payload)
            return True

def get_feature_class():
    return Definition()
