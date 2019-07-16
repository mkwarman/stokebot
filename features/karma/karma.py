import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import helpers, featurebase
from karma.dao import increment, decrement, get_by_subject
from karma.sqlalchemy_declarative import Base

# Great info here: https://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/

engine = create_engine("sqlite:///karma.db")
# Bind the engine to the metadata so we can use the declartives in sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits, rollback, etc

MAX_KARMA_CHANGE = 5

KARMA_REGEX = re.compile(r'((?:<(?:@|#)[^ ]+>)|\w+) ?(\+\++|--+)')

def handle_karma_change(match, payload):
    subject = match[0].lower()
    client = payload['web_client']
    operator = match[1]
    max_change_triggered = False

    # If user tried to change their own karma, reply and return without changing anything
    if ('user' in payload['data'] and subject[2:-1] == payload['data']['user'].lower()):
        reply = "It's rude to toot your own horn" if operator[0] == '+' else "Don't be so hard on yourself!"
        #helpers.post_reply(payload, reply)
        return reply

    # Limit max karma change
    delta = len(operator) - 1
    if delta > MAX_KARMA_CHANGE:
        max_change_triggered = True
        delta = MAX_KARMA_CHANGE

    session = DBSession()

    # If subject is a user, get their friendly name before replying
    name = helpers.to_first_name_if_tag(subject, client)
    reply = "{0}'s karma has".format(name)

    if operator[0] == '+':
        reply += " increased to "
        increment(session, subject, delta)
    else:
        reply += " decreased to "
        decrement(session, subject, delta)

    reply += str(get_by_subject(session, subject))
    if max_change_triggered:
        reply += (" (max karma change of {0} points enforced!)".format(MAX_KARMA_CHANGE))

    #helpers.post_reply(payload, reply)

    # Close the DBSession
    session.close()

    return reply

class Karma(featurebase.FeatureBase):
    def on_message(self, text, payload):
        # Check for possible karma changes
        karma_matches = KARMA_REGEX.findall(text)
        responses = []
        for match in karma_matches:
            responses.append(handle_karma_change(match, payload))

        if len(responses) > 0:
            helpers.post_reply(payload, "\n".join(responses))


def get_feature_class():
    return Karma()
