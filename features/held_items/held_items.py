import os
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import featurebase
from held_items.dao import insert_item, swap_items, get_item_count, \
        get_held_items
from held_items.sqlalchemy_declarative import Base

# Great info here:
#   https://www.pythoncentral.io/introductory-tutorial-python-sqlalchemy/

engine = create_engine("sqlite:///data/held_items.db")
# Bind the engine to the metadata so we can use the declartives in
#   sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits,
#   rollback, etc

TRIGGER_REGEX = re.compile(r'(?i)^gives <@' + re.escape(os.getenv("BOT_ID"))
                           + r'\|[^>]+> (.+)')
HELD_ITEMS_TRIGGERS = ["items held", "held items"]
MAX_HELD_ITEMS = 5


def handle_give(item, data, client):
    session = DBSession()

    count = get_item_count(session)

    user_id = data['user']

    user_name = client.get_first_name_from_id(user_id)

    reply = "_takes {0} from {1}".format(item, user_name)

    # We use count + 1 since this is an add flow and the new total would be
    #   count + 1
    if count + 1 > MAX_HELD_ITEMS:
        return_item = swap_items(session, item, user_name)
        reply += " and gives them {0}_".format(return_item)
    else:
        insert_item(session, item, user_name)
        reply += "_"

    session.close()
    client.post_reply(data, reply)


def handle_list(data, client):
    session = DBSession()

    items = get_held_items(session)

    session.close()

    reply = ("I'm currently holding {0}".format(', '.join(items)) if items
             else "I'm not currently holding anything!")

    client.post_reply(data, reply)


class HeldItems(featurebase.FeatureBase):
    def slack_connected(self, client):
        self.client = client

    def on_me_message(self, text, data):
        item_operation = TRIGGER_REGEX.search(text)
        if item_operation:
            handle_give(item_operation.group(1), data, self.client)

    def on_command(self, command, data):
        for trigger in HELD_ITEMS_TRIGGERS:
            if command.lower().startswith(trigger):
                handle_list(data, self.client)
                return True


def get_feature_class():
    return HeldItems()
