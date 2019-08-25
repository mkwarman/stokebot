import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import helpers, featurebase
from definition.dao import get_by_trigger, insert_definition, get_triggers, check_blacklist, insert_blacklist, remove_blacklist, check_ignored, insert_ignored, remove_ignored
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
            print('found word in blacklist:', word)
            return
        # Check for unknown word in dictionary
        found = check_dictionary(word)
        if found:
            print('found word in dictionary:', word)
            insert_blacklist(session, word, 'dictionary')
            return
        #TODO: ask for definition
        print('no definition found')

    session.close()

def handle_ignore(should_ignore, payload):
    user = helpers.get_user_from_payload(payload)

    if not user:
        # If this is not a person
        return

    session = DBSession()
    reply = "Ok, {0}, I will ".format(helpers.get_first_name_from_id(user, payload['web_client']))

    if should_ignore:
        insert_ignored(session, user)
        reply += "stop "
    else:
        remove_ignored(session, user)
        reply += "resume "

    session.close()
    reply += "listening to you."
    helpers.post_reply(payload, reply)

def handle_blacklist(should_blacklist, trigger, payload):
    user = helpers.get_user_from_payload(payload)

    if not user:
        # If this is not a person
        return

    session = DBSession()
    reply = "Ok, {0}, I will ".format(helpers.get_first_name_from_id(user, payload['web_client']))

    if should_blacklist:
        insert_blacklist(session, trigger, user)
        reply += "add {0} to ".format(trigger)
    else:
        remove_blacklist(session, trigger)
        reply += "remove {0} from ".format(trigger)

    session.close()
    reply += "the blacklist."
    helpers.post_reply(payload, reply)


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
        elif command.startswith("blacklist add"):
            handle_blacklist(True, command[14:], payload)
            return True
        elif command.startswith("blacklist remove"):
            handle_blacklist(False, command[17:], payload)
            return True

def get_feature_class():
    return Definition()
