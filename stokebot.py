import os
import time
import definition_model
import blacklisted_model
import dao
import api
import word_check
import re
from slackclient import SlackClient

# constants
BOT_NAME = "stokebot"
TARGET_USER_NAME = "mkwarman"
EXAMPLE_COMMAND = "do"
ADD_COMMAND = ("add")
BLACKLIST_COMMAND = ("blacklist")
SECONDARY_ADD_COMMAND = ("means", "is")
READ_COMMAND = ("what is", "define")
VERBOSE_COMMAND = ("verbose")
STATUS_COMMAND = ("status")
SHOW_ALL_COMMAND = ("showall", "show all", "show all definitions", "show all words")
DELETE_COMMAND = ("delete")
STOP_COMMAND = ("stop")

# globals
global at_bot_id
global at_target_user_id

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_text(text, channel, message_data):
    print("Handling text")
    if text.startswith("<@" + at_bot_id + ">"):
        print("Received command: " + text)
        return handle_command(text, channel, message_data)
    elif 'user' in message_data and at_target_user_id in message_data['user']:
        print("Target user said: " + text)
        check_target_user_text(text, channel, message_data)

    return True

def check_target_user_text(text, channel, message_data):
    print("Checking target user text")
    words = word_check.sanitize_and_split_words(text)
    unknown_words = word_check.find_unknown_words(words)
    for word in unknown_words:
        print("About to check_dictionary for \"" + word + "\"")
        if not word_check.check_dictionary(word) and len(dao.read_definition(word)) == 0:
            # definition was not found
            response = "Hey <@" +message_data['user'] + ">! What does \"" + word + "\" mean?"
            api.send_reply(response, channel)

#Find out why we're getting unknown command
def handle_command(text, channel, message_data):
    print("In handle_command")
    command = text.split("<@" + at_bot_id + ">")[1].strip().lower()
    print("Parsed command: " + command)
    if command == STOP_COMMAND:
        return False
    elif command.startswith(ADD_COMMAND):
        handle_add_definition(command, channel, message_data)
    elif command.startswith(READ_COMMAND):
        handle_read_definition(command, channel, message_data)
    elif command.startswith(STATUS_COMMAND):
        handle_status_inquiry(channel)
    elif len(command.split(" ")) > 2 and command.split(" ")[1] in SECONDARY_ADD_COMMAND:
        handle_secondary_add_definition(command, channel, message_data)
    elif command in SHOW_ALL_COMMAND:
        handle_show_all(channel)
    elif command.startswith(VERBOSE_COMMAND):
        handle_verbose(command, channel)
    elif command.startswith(DELETE_COMMAND):
        handle_delete(command, channel, message_data)
    elif command.startswith(BLACKLIST_COMMAND):
        handle_blacklist(command, channel, message_data)
    else:
        handle_unknown_command(channel)

    return True

def handle_unknown_command(channel):
    api.send_reply("Command not recognized", channel)
            
def handle_delete(command, channel, message_data):
    # Extract just the word from the command
    #word_id = command[len([command_text for command_text in DELETE_COMMAND if command.startswith(command_text)][0]):].strip()
    word_id = command[7:]

    if api.is_admin(message_data['user']):
        definition = dao.get_by_id(word_id)
        if not definition:
            api.send_reply("ID " + word_id + " does not exist.", channel)
            return
        dao.delete_by_id(word_id)
        response = "Ok <@" +message_data['user'] + ">, I deleted ID " + word_id + ": \"" + definition.word + "\"."
    else:
        response = "Sorry <@" +message_data['user'] + ">, only admins can delete words."

    api.send_reply(response, channel)

def handle_status_inquiry(channel):
    api.send_reply("I'm here!", channel)

def handle_verbose(command, channel):
    # Extract just the word from the command
    #word = command[len([command_text for command_text in VERBOSE_COMMAND if command.startswith(command_text)][0]):].strip()
    word = command[8:]

    # Read the definition from the database
    definitions = dao.read_definition(word)

    # Reply definitions from the database
    for definition in definitions:
        print(definition)
        api.send_reply(str(definition), channel)


def handle_show_all(channel):
    definitions = dao.select_all()
    
    # Reply definitions from the database
    for definition in definitions:
        print(definition)
        api.send_reply((definition.word + " means " + definition.meaning), channel)

def listen_for_text(slack_rtm_output):
    """
    	Listen for messages sent by certian users. If the message was
    	sent by one of those users, then do more.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            #if output and 'text' in output and 'user' in output and at_target_user_id in output['user']:
            if output and 'text' in output:
                return output['text'], output['channel'], output
                # return None, None
    return None, None, None

def handle_read_definition(command, channel, message_data):
    # Extract just the relevent section from the text
    #command = text.split("<@" + at_bot_id + ">")[1].strip()

    # Extract just the word from the command
    word = command[len([command_text for command_text in READ_COMMAND if command.startswith(command_text)][0]):].strip()
    sanitized_word = re.sub("[^a-z -'’]", "", word)
    print("sanitized_word: " + sanitized_word)
    
    # Read the definition from the database
    definitions = dao.read_definition(sanitized_word)
    print(definitions)
    
    # Reply definitions from the database
    for definition in definitions:
        print(definition)
        api.send_reply((definition.word + " means " + definition.meaning), channel)

def handle_secondary_add_definition(command, channel, message_data):
    #command = text.split("<@" + at_bot_id + ">")[1].strip()
    command_data = command.split(" ")

    word = command_data[0]
    meaning = " ".join(command_data[2:])

    add_definition(word, meaning, channel, message_data)

def handle_add_definition(command, channel, message_data):
    # Extract just the relevent section from the text
    #command = text.split("<@" + at_bot_id + ">")[1].strip()

    # Extract just the word and the meaning from the command
    #word_and_meaning = command[len([command_text for command_text in ADD_COMMAND if command.startswith(command_text)][0]):].split(":")
    word_and_meaning = command[3:].split(":")
    word = word_and_meaning[0].strip()
    meaning = word_and_meaning[1].strip()

    add_definition(word, meaning, channel, message_data)

def add_definition(word, meaning, channel, message_data):
    # Instantiate definition object
    definition_object = definition_model.Definition()
    
    # Get friendly names of user and channel 
    user_name = api.get_user_name(message_data['user'])
    channel_name = api.get_name_from_id(message_data['channel'])

    # Populate definition object
    definition_object.new(word, meaning, user_name, channel_name)

    api.send_reply("Ok <@" + message_data['user'] + ">, I'll remember that " + word + " means " + meaning, channel)
    print("attempting to insert into database: " + str(definition_object))
    
    # Send definition object to database
    dao.insert_definition(definition_object)

def handle_blacklist(command, channel, message_data):
    if api.is_admin(message_data['user']):
        sub_command = command[10:]
        print("sub_command: " + sub_command)
        if sub_command.startswith("add"):
            # add to blacklist
            blacklist_add(sub_command[4:], channel, message_data)
        elif sub_command.startswith("get"):
            # read from blacklist
            blacklist_read(sub_command[4:], channel, message_data)
        elif sub_command.startswith("delete"):
            # delete from blacklist
            blacklist_delete(sub_command[7:], channel, message_data)
        elif sub_command.startswith("showall"):
            # show full blacklist
            blacklist_showall(channel)
        else:
            api.send_reply("Try \"backlist add\", \"backlist get\", \"backlist delete\", or \"blacklist showall\"", channel)
    
    else:
        api.send_reply("Sorry <@" +message_data['user'] + ">, only admins can edit the blacklist.", channel)

def blacklist_add(word, channel, message_data):
    print("in blacklist_add, word: " + word)
    # Instantiate blacklist object
    blacklisted_object = blacklisted_model.Blacklisted()

    user_name = api.get_user_name(message_data['user'])
    channel_name = api.get_name_from_id(message_data['channel'])

    blacklisted_object.new(word, user_name, channel_name)

    dao.insert_blacklisted(blacklisted_object)
    api.send_reply("Ok <@" + message_data['user'] + ">, I've added " + word + " to the blacklist", channel)

def blacklist_read(word, channel, message_data):
    blacklisted = dao.get_blacklisted_by_word(word)

    print(blacklisted)
    api.send_reply(str(blacklisted), channel)

def blacklist_delete(blacklisted_id, channel, message_data):
    blacklisted = dao.get_blacklisted_by_id(blacklisted_id)
    if not blacklisted:
        api.send_reply("ID " + blacklisted_id + " does not exist.", channel) 
        return
    dao.delete_blacklisted_by_id(blacklisted_id)

    api.send_reply("Ok <@" + message_data['user'] + ">, I've removed " + blacklisted.word + " from the blacklist", channel)   

def blacklist_showall(channel):
    blacklist = dao.select_all_blacklisted()

    for blacklisted in blacklist:
        print(str(blacklisted))
        api.send_reply(str(blacklisted), channel)

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = .5 # .5 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StokeBot connected and running!")
        global at_bot_id
        global at_target_user_id
        at_bot_id = api.get_user_id(BOT_NAME) # Get the bot's ID
        at_target_user_id = api.get_user_id(TARGET_USER_NAME) # Get the target user's ID

        run = True
        while run:
            text, channel, message_data = listen_for_text(slack_client.rtm_read())
            if text and channel:
                run = handle_text(text, channel, message_data)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or Bot ID?")

