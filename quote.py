""" Quote specific functions """
import api
import common
import dao
from quote_model import Quote

RANDOM_QUOTE_SUBCOMMAND = "random"
VERBOSE_QUOTE_SUBCOMMAND = "verbose"
ADD_QUOTE_SUBCOMMAND = "add"
DELETE_QUOTE_SUBCOMMAND = "delete"

COMMAND_NOT_UNDERSTOOD_MESSAGE = "I'm sorry, I didn't understand that!"

def handle_quote(command, channel, message_data):
    """
        Handle quote commands from users. Some examples:

        * quote add author "test"
        * quote author
        * quote random
        * quote verbose author
        * quote delete quote_id
    """

    split_command = command.split(" ")

    if len(split_command) < 2:
        api.send_reply(COMMAND_NOT_UNDERSTOOD_MESSAGE, channel)
        return

    subcommand = split_command[1]

    # If command is add and there are enough elements in the split command
    if subcommand == ADD_QUOTE_SUBCOMMAND:
        insert_quote(split_command, channel, message_data)
    # If command is to get verbose
    elif subcommand == VERBOSE_QUOTE_SUBCOMMAND:
        get_quote_verbose(split_command, channel)
    # If command is to delete quote
    elif subcommand == DELETE_QUOTE_SUBCOMMAND:
        delete_quote_by_id(split_command, channel)
    # If command is to get quote by author (subcommand)
    else:
        get_quote(subcommand, channel)


def insert_quote(split_command, channel, message_data):
    """ Parse and insert a new quote """

    # There should be four elements in the split command
    if len(split_command) < 4:
        api.send_reply(COMMAND_NOT_UNDERSTOOD_MESSAGE, channel)
        return

    # Parse author
    author = split_command[2]
    # Parse quote, removing any double or single ticks
    quote = " ".join(split_command[3:]).replace("\"", "").replace("\'", "")

    response = "Ok <@" + message_data['user'] + ">, I'll remember " + author + "'s quote.'"

    new_quote = Quote()
    new_quote.new(author, quote, channel)

    # process any other misc logic

    dao.insert_quote(new_quote)

    api.send_reply(response, channel)

def get_quote(author, channel):
    """ Handle user asking for quote by author """

    # If quote from user or random if requested
    quote = dao.get_random_quote() if author == RANDOM_QUOTE_SUBCOMMAND else \
            dao.get_random_quote(author)

    if quote is None:
        response = "I dont know any quotes by " + author
    else:
        response = "\"" + quote.quote + "\" - _" \
                   + common.to_first_name_if_tag(quote.author) + "_"

    api.send_reply(response, channel)

def get_quote_verbose(split_command, channel):
    """ Get all quotes by author and return them in their raw form """

    if len(split_command) < 3:
        api.send_reply(COMMAND_NOT_UNDERSTOOD_MESSAGE, channel)
        return

    author = split_command[2] # parse author
    quotes = dao.get_quotes(author)

    response = "Quotes by " + author + ":"

    for quote in quotes:
        response += str(quote) + "\n"

    api.send_reply(response, channel)

def delete_quote_by_id(split_command, channel):
    """ Delete quote based on input ID """

    if len(split_command) < 2:
        api.send_reply(COMMAND_NOT_UNDERSTOOD_MESSAGE, channel)
        return

    quote_id = split_command[2]

    if not quote_id:
        response = "No ID provided!"
    elif dao.quote_exists:
        dao.delete_quote_by_id(quote_id)
        response = "Ok, I deleted quote " + str(quote_id) + "."
    else:
        response = "No quote with ID " + str(quote_id) + " exists!"

    api.send_reply(response, channel)
