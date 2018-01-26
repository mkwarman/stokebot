# pylint: disable=C0325
""" Karma specific functions """
import api
import common
import dao

MAX_KARMA_CHANGE = 5
TOP_KARMA_SUBCOMMAND = "top"
TOP_KARMA_LIMIT = 5

def handle_karma_change(karma, channel, message_data):
    """ Handle karma updates from users """
    key = karma[0].lower()
    operator = karma[1]
    delta = len(operator) - 1
    response = (common.to_first_name_if_tag(key)) + "'s karma has "

    if (key == "<@" + message_data['user'].lower() + ">"):
        # Don't let users vote on themselves
        if (operator[0] == '+'):
            response = "It's rude to toot your own horn."
        else:
            response = "Don't be so hard on yourself!"
        api.send_reply(response, channel)
        return

    if (delta > MAX_KARMA_CHANGE):
        api.send_reply("Max karma change of 10 points enforced!", channel)
        delta = 10

    if (operator[0] == '+'):
        response += "increased"
    else:
        delta = -delta
        response += "decreased"

    dao.update_karma(key, delta)

    response += " to " + str(dao.get_karma(key))

    api.send_reply(response, channel)

def handle_karma(text, channel):
    """ Handle user asking for object/user karma """
    key = text.split(" ")[1]

    if key == TOP_KARMA_SUBCOMMAND:
        handle_top_karma(channel)
        return

    response = common.to_first_name_if_tag(key)

    karma = dao.get_karma(key)

    if karma is None:
        response += " has no karma score!"
    else:
        response += "'s karma is " + str(karma)

    api.send_reply(response, channel)

def handle_top_karma(channel):
    """ Handle user asking for top karma entries """
    response = "Top karma entries:"
    top_karma_entities = dao.get_top_karma(TOP_KARMA_LIMIT)
    for entity in top_karma_entities:
        response += ("\n" + common.to_real_name_if_tag(entity[0]) + ": " + str(entity[1]))

    api.send_reply(response, channel)
