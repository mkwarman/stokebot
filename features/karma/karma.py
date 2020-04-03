import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import builders, featurebase, helpers
from karma.dao import increment, decrement, get_by_subject, get_top
from karma.sqlalchemy_declarative import Base

# Great info here:
#   https://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/

engine = create_engine("sqlite:///data/karma.db")
# Bind the engine to the metadata so we can use the declartives in
#   sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits,
#   rollback, etc

MAX_KARMA_CHANGE = 5
TOP_KARMA_LIMIT = 5
TOP_KARMA_SUBCOMMAND = "top"

KARMA_REGEX = re.compile(r'((?:<(?:@|#)[^ ]+>)|\w+) ?(\+\++|--+)')


def handle_karma_matches(matches, data, client):
    session = DBSession()
    responses = []

    for match in matches:
        responses.append(handle_karma_change(match, session, data, client))

    session.close()

    if (len(responses) > 0):
        client.post_reply(data, "\n".join(responses))


def handle_karma_change(match, session, data, client):
    subject = match[0].lower()
    operator = match[1]
    max_change_triggered = False

    # If user tried to change their own karma,
    #   reply and return without changing anything
    user = helpers.get_user_from_data(data)
    if (user and subject[2:-1] == user.lower()):
        reply = "It's rude to toot your own horn" if operator[0] == '+' \
                else "Don't be so hard on yourself!"
        return reply

    # Limit max karma change
    delta = len(operator) - 1
    if delta > MAX_KARMA_CHANGE:
        max_change_triggered = True
        delta = MAX_KARMA_CHANGE

    # If subject is a user, get their friendly name before replying
    name = client.to_first_name_if_tag(subject)
    reply = "{0}'s karma has".format(name)

    if operator[0] == '+':
        reply += " increased to "
        increment(session, subject, delta)
    else:
        reply += " decreased to "
        decrement(session, subject, delta)

    reply += str(get_by_subject(session, subject))
    if max_change_triggered:
        reply += (" (max karma change of {0} points enforced!)"
                  .format(MAX_KARMA_CHANGE))

    return reply


def handle_command(command, data, client):
    key = command.split(" ")[1].lower()  # 'karma '

    if (key == TOP_KARMA_SUBCOMMAND):
        handle_top_karma(data, client)
        return

    response = client.to_first_name_if_tag(key)

    session = DBSession()
    karma = get_by_subject(session, key)
    session.close()

    if karma is None:
        response += " has no karma score!"
    else:
        response += "'s karma is " + str(karma)

    client.post_reply(data, response)


def handle_top_karma(data, client):
    response = "Top karma entries:"
    session = DBSession()
    karma_entries = get_top(session, TOP_KARMA_LIMIT)
    session.close()

    for entry in karma_entries:
        name = client.to_real_name_if_tag(entry)
        response += ("\n{0}: {1}".format(name, karma_entries[entry]))

    client.post_reply(data, response)


class Karma(featurebase.FeatureBase):
    def slack_connected(self, client):
        self.client = client

    def on_message(self, text, data):
        # Check for possible karma changes
        karma_matches = KARMA_REGEX.findall(text)
        if (len(karma_matches) > 0):
            handle_karma_matches(karma_matches, data, self.client)

    def on_command(self, command, data):
        if (command.lower().startswith('karma')):
            handle_command(command, data, self.client)
            return True

    def get_help(self):
        bb = builders.BlocksBuilder()
        sb = builders.SectionBuilder()
        sb.add_text("*Awarding Karma:*\n")  # noqa: E501
        sb.add_text("To give someone or something karma, use two or more plus signs immediately after the subject:\n")  # noqa: E501
        sb.add_text("    • \"Great job <@{botid}>++!\" would award {botname} one karma\n")  # noqa: E501
        sb.add_text("    • \"slackbots+++++ are the coolest\" would award \"Slackbots\" four karma\n")  # noqa: E501
        sb.add_text("Similarly, you can use minus signs to decrement karma:\n")  # noqa: E501
        sb.add_text("    • \"I sure hate homework-----\" would subtract four karma from \"homework\"\n")  # noqa: E501
        sb.add_text("You can perform multiple karma operations in one message:\n")  # noqa: E501
        sb.add_text("    • \"coffee+++ bills---\" would give \"coffee\" two karma and subtract two karma from \"bills\" \n")  # noqa: E501
        sb.format_text(botid=os.getenv('BOT_ID'),
                       botname=os.getenv('BOT_NAME')
                       )
        bb.add_block(sb.section)
        bb.add_divider()

        sb.add_text("\n*Checking Karma:*\n")  # noqa: E501
        sb.add_text("To check karma, say:\n")  # noqa: E501
        sb.add_text("    • \"<@{botid}> karma _subject_\"\n")  # noqa: E501
        sb.add_text("To see the karma leaderboard, say:\n")  # noqa: E501
        sb.add_text("    • \"<@{botid}> karma top\"\n")  # noqa: E501
        sb.format_text(botid=os.getenv('BOT_ID'))
        bb.add_block(sb.section)

        return bb.blocks


def get_feature_class():
    return Karma()
