import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import helpers, featurebase
from karma.dao import increment, decrement, get_by_subject, get_top
from karma.sqlalchemy_declarative import Base

# Great info here: https://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/

engine = create_engine("sqlite:///data/karma.db")
# Bind the engine to the metadata so we can use the declartives in sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits, rollback, etc

MAX_KARMA_CHANGE = 5
TOP_KARMA_LIMIT = 5
TOP_KARMA_SUBCOMMAND = "top"

KARMA_REGEX = re.compile(r'((?:<(?:@|#)[^ ]+>)|\w+) ?(\+\++|--+)')

def handle_karma_matches(matches, payload):
    session = DBSession()
    responses = []

    for match in matches:
        responses.append(handle_karma_change(match, payload, session))

    session.close()

    if (len(responses) > 0):
        helpers.post_reply(payload, "\n".join(responses))

def handle_karma_change(match, payload, session):
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

    return reply

def handle_command(command, payload):
    key = command.split(" ")[1].lower() # 'karma '
    client = payload['web_client']

    if (key == TOP_KARMA_SUBCOMMAND):
        handle_top_karma(client, payload)
        return

    response = helpers.to_first_name_if_tag(key, client)

    session = DBSession()
    karma = get_by_subject(session, key)
    session.close()

    if karma is None:
        response += " has no karma score!"
    else:
        response += "'s karma is " + str(karma)

    helpers.post_reply(payload, response)

def handle_top_karma(client, payload):
    response = "Top karma entries:"
    session = DBSession()
    karma_entries = get_top(session, TOP_KARMA_LIMIT)
    session.close()
    
    for entry in karma_entries:
        name = helpers.to_real_name_if_tag(entry, client)
        response += ("\n{0}: {1}".format(name, karma_entries[entry]))

    helpers.post_reply(payload, response)

class Karma(featurebase.FeatureBase):
    def on_message(self, text, payload):
        # Check for possible karma changes
        karma_matches = KARMA_REGEX.findall(text)
        if (len(karma_matches) > 0):
            handle_karma_matches(karma_matches, payload)

    def on_command(self, command, payload):
        print("command:", command)
        if (command.lower().startswith('karma')):
            handle_command(command, payload)
            return True

def get_feature_class():
    return Karma()
