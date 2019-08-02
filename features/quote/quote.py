import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import helpers, featurebase
from quote.dao import add_quote, get_quote_by_author
from quote.sqlalchemy_declarative import Base

# Great info here: https://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/

engine = create_engine("sqlite:///data/quote.db")
# Bind the engine to the metadata so we can use the declartives in sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits, rollback, etc

QUOTE_TRIGGER = 'quote'
DATE_FORMAT = "%m/%d/%y"

def handle_add(command, payload):
    print("got quote add")
    split_command = command.split("\"")
    author = split_command[0].strip()
    quote = split_command[1].strip()

    session = DBSession()
    add_quote(session, author, quote)
    session.close()

    reply = "Ok, I saved quote: \"{0}\" by {1}".format(quote, author)
    helpers.post_reply(payload, reply)

def handle_get(command, payload):
    print("got quote get")
    author = command
    print("looking for quotes by author {0}".format(author))
    session = DBSession()
    quote = get_quote_by_author(session, author)
    session.close()

    reply = ("\"{0}\" - _{1}, {2}_".format(quote.quote, quote.author, quote.date_time_added.strftime(DATE_FORMAT))
             if quote else "I don't know any quotes by {0}".format(author))
    helpers.post_reply(payload, reply)

class Quotes(featurebase.FeatureBase):
    def on_command(self, command, payload):
        if command.lower().startswith(QUOTE_TRIGGER):
            stripped_command = command[len(QUOTE_TRIGGER):].strip()
            if "\"" in command:
                handle_add(stripped_command, payload)
            else:
                handle_get(stripped_command, payload)
            return True

def get_feature_class():
    return Quotes()
