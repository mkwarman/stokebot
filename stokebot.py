import os
import time
import definition_model
import dao
import api
import word_check
from slackclient import SlackClient

# constants
BOT_NAME = "stokebot"
TARGET_USER_NAME = "mkwarman"
ADMIN_USER_NAME = "mkwarman"
EXAMPLE_COMMAND = "do"
ADD_COMMAND = ("add")
SECONDARY_ADD_COMMAND = ("means", "is")
READ_COMMAND = ("what is", "define")
VERBOSE_COMMAND = ("verbose")
STATUS_COMMAND = ("status")
SHOW_ALL_COMMAND = ("show all", "show all definitions", "show all words")
DELETE_COMMAND = ("delete")

# globals
global at_bot_id
global at_target_user_id

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_target_user_text(text, channel, message_data):
    print("Handling target user text")
    if at_bot_id in text:
        handle_command(text, channel, message_data)
    else:
        check_target_user_text(text, channel, message_data)

def check_target_user_text(text, channel, message_data):
    print("Checking target user text")
    words = word_check.sanitize_and_split_words(text)
    unknown_words = word_check.find_unknown_words(words)
    for word in unknown_words:
        print("About to check_dictionary for \"" + word + "\"")
        if not word_check.check_dictionary(word):
            # definition was not found
            response = "Hey <@" +message_data['user'] + ">! What does \"" + word + "\" mean?"
            api.send_reply(response, channel)

#Find out why we're getting unknown command
def handle_command(text, channel, message_data):
    print("in handle_command")
    command = text.split("<@" + at_bot_id + ">")[1].strip().lower()
    print("command: " + command)
    if command.startswith(ADD_COMMAND):
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
    else:
        handle_unknown_command(channel)

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

def listen_for_user(slack_rtm_output):
    """
    	Listen for messages sent by certian users. If the message was
    	sent by one of those users, then do more.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and 'user' in output and at_target_user_id in output['user']:
                print("Target user said: " + output['text'])
                return output['text'], output['channel'], output
                # return None, None
    return None, None, None

def handle_read_definition(command, channel, message_data):
    # Extract just the relevent section from the text
    #command = text.split("<@" + at_bot_id + ">")[1].strip()

    # Extract just the word from the command
    word = command[len([command_text for command_text in READ_COMMAND if command.startswith(command_text)][0]):].strip()
    print("word: " + word)
    
    # Read the definition from the database
    definitions = dao.read_definition(word)
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
    word_and_meaning = command[len([command_text for command_text in ADD_COMMAND if command.startswith(command_text)][0]):].split(":")
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

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = .5 # .5 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StokeBot connected and running!")
        global at_bot_id
        global at_target_user_id
        at_bot_id = api.get_user_id(BOT_NAME) # Get the bot's ID
        at_target_user_id = api.get_user_id(TARGET_USER_NAME) # Get the target user's ID

        while True:
            text, channel, message_data = listen_for_user(slack_client.rtm_read())
            if text and channel:
                handle_target_user_text(text, channel, message_data)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or Bot ID?")

