""" Quote specific functions """
import api
import common
import dao
import quote_model

RANDOM_QUOTE_SUBCOMMAND = "random"

def handle_quote_add(quote, channel, message_data):
    """ Handle adding new quotes from users """
    author = "" # parse author of quote
    quote = "" # parse quote
    response = "" # response here

    new_quote = quote_model.Quote()
    new_quote.new(author, quote, channel)

    # process any other misc logic

    dao.insert_quote(new_quote)

    api.send_reply(response, channel)

def handle_karma(text, channel):
    """ Handle user asking for quote by author """
    author = "" # parse author of quote

    # If random quote was requested
    #if author == RANDOM_QUOTE_SUBCOMMAND:
        # get random quote

    quote = dao.get_quote(author)

    if quote is None:
        response = "I dont know any quotes by " + author
    else:
        response = "" # response here

    api.send_reply(response, channel)

#def handle_quote_verbose(text, channel):
    #stuff
