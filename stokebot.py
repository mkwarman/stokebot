import os
import time
import definition_model
import blacklisted_model
import user_model
import dao
import api
import word_check
import re
from slackclient import SlackClient

# constants
BOT_NAME = os.environ.get('BOT_NAME')#"stokebot"
BOT_OWNER_NAME = os.environ.get('BOT_OWNER_NAME')#"mkwarman"
TARGET_USER_NAME = os.environ.get('TARGET_USER_NAME')#"austoke"
READ_WEBSOCKET_DELAY = .5 # .5 second delay between reading from firehose
CONNECTION_ATTEMPT_RETRY_DELAY = 1

ADD_COMMAND = ("add")
MEANS_COMMAND = (" means ")
IS_COMMAND = (" is ")
ARE_COMMAND = (" are ")
READ_COMMAND = ("what is", "define")
BLACKLIST_COMMAND = ("blacklist")
VERBOSE_COMMAND = ("verbose")
STATUS_COMMAND = ("status")
SHOW_ALL_COMMAND = ("showall", "show all", "show all definitions", "show all words")
DELETE_COMMAND = ("delete")
STOP_COMMAND = ("stop")
SAY_COMMAND = ("say")
HELP_COMMAND = ("help")
IGNORE_COMMAND = ("ignore")
LISTEN_COMMAND = ("listen to")
CHECK_COMMAND = ("check")

# globals
global at_bot_id
global at_target_user_id
global defined_words
global blacklisted_words
global ignored_users

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_text(text, channel, message_data):
    print("Handling text")
    print("User: " + message_data['user'])
    if text.startswith("<@" + at_bot_id + ">"):
        print("Received command: " + text)
        return handle_command(text, channel, message_data)
    elif 'user' in message_data and message_data['user'] not in ignored_users:
        check_user_text(text, channel, message_data, False)

    return True

def check_user_text(text, channel, message_data, testing_mode):
    print("Checking user text")
    words = word_check.sanitize_and_split_words(text)
    unique_words = set(words)


    for word in list(unique_words):
        if word in defined_words:
            if testing_mode:
                api.send_reply("Found \"" + word + "\" in defined_words", channel)
            print("Found \"" + word + "\" in defined_words")
            definitions = dao.read_definition(word)
            dao.increment_word_usage_count(word, words.count(word))
            reply_definitions(definitions, channel)
            unique_words.remove(word)
        elif word in blacklisted_words:
            if testing_mode:
                api.send_reply("Found \"" + word + "\" in blacklisted_words", channel)
            print("Found \"" + word + "\" in blacklisted_words")
            unique_words.remove(word)

    if ('user' in message_data and at_target_user_id in message_data['user']) or testing_mode:
        print("Target user said: " + text)
        handle_target_user_text(unique_words, channel, message_data, testing_mode)

def handle_target_user_text(words, channel, message_data, testing_mode):
    unknown_words = word_check.find_unknown_words(words)
    for word in unknown_words:
        print("About to check_dictionary for \"" + word + "\"")
        if not word_check.check_dictionary(word):
            # definition was not found
            response = "Hey <@" +message_data['user'] + ">! What does \"" + word + "\" mean?"
            api.send_reply(response, channel)
        else:
            # Insert dictionary word into the blacklist so we dont keep using database queries
            if testing_mode:
                api.send_reply("Found dictionary definition for \"" + word + "\". Adding to blacklist...", channel)
            print("Found dictionary definition for \"" + word + "\". Adding to blacklist...")
            blacklisted_object = blacklisted_model.Blacklisted()
            channel_name = api.get_name_from_id(message_data['channel'])
            user_name = "[dictionary_api]"
            blacklisted_object.new(word, user_name, channel_name)
            dao.insert_blacklisted(blacklisted_object)
            blacklisted_words.append(word)

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
    elif MEANS_COMMAND in command:
        handle_means(command, channel, message_data)
    elif IS_COMMAND in command:
        handle_is(command, channel, message_data)
    elif ARE_COMMAND in command:
        handle_are(command, channel, message_data)
    elif command in SHOW_ALL_COMMAND:
        handle_show_all(channel)
    elif command.startswith(VERBOSE_COMMAND):
        handle_verbose(command, channel)
    elif command.startswith(DELETE_COMMAND):
        handle_delete(command, channel, message_data)
    elif command.startswith(IGNORE_COMMAND):
        handle_ignore(command, channel, message_data)
    elif command.startswith(LISTEN_COMMAND):
        handle_listen(command, channel, message_data)
    elif command.startswith(SAY_COMMAND):
        handle_say(text, channel, message_data)
    elif command.startswith(BLACKLIST_COMMAND):
        handle_blacklist(command, channel, message_data)
    elif command.startswith(CHECK_COMMAND):
        handle_check(command, channel, message_data)
    elif command == HELP_COMMAND:
        handle_help(channel)
    else:
        handle_unknown_command(channel)

    return True

def handle_check(command, channel, message_data):
    text = command[6:]
    check_user_text(text, channel, message_data, True)

def handle_help(channel):
    response = "Basic Commands:\n" \
               + ">`@stokebot add [word]: [meaning]` --- Use this command to add a definition to the database\n" \
               + ">`@stokebot [word] means [meaning]` --- Use this command to add a definition to the database\n" \
               + ">`@stokebot (define/what is) [word]` --- Use this command to look up a word in the database\n" \
               + ">`@stokebot ignore me/[user]` --- Use this command to stop stokebot from defining you or someone else's text. He will still " \
               + "listen to commands\n" \
               + ">`@stokebot listen to me/[user]` --- Use this command to have stokebot resume defining your or someone else's text after" \
               + "asking him to \"ignore\" it previously\n" \
               + ">`@stokebot stop` --- Use this command if I get too annoying or messed up. I will have to be manually " \
               + "restarted afterward, but that's ok... I'm not programmed to have feelings, after all...:slightly_frowning_face:\n" \
               + "\nThere are a few other more advanced administration commands, but since this bot is " \
               + "still in development they are outside of the scope of this help message. " \
               + "Feel free to pester <@" + api.get_user_id(BOT_OWNER_NAME) + "> with questions!"

    api.send_reply(response, channel)

def handle_say(text, channel, message_data):
    print("In handle_say")
    raw_phrase = text.split("<@" + at_bot_id + ">")[1].strip()[4:]
    # Extract just the phrase from the command
    #phrase = command[len([command_text for command_text in SAY_COMMAND if command.startswith(command_text)][0]):].strip()
    phrase_data = raw_phrase.lower().split(" ")
    print("phrase_data: ", phrase_data)

    at_user = "<@" + message_data['user'] + ">"

    replacements = {"you" : "I",
                    "you're": "I am",
                    "you’re": "I am",
                    "your": "My",
                    "my": at_user + "'s",
                    "i" : at_user}

    replacements2 = {"are" : "am",
                     "am": "is"}

    if phrase_data[0] and phrase_data[0] in replacements:
        replacement_word = replacements[phrase_data[0]]
        print("Replacing \"" + phrase_data[0] + "\" with \"" + replacement_word + "\"")
        phrase_data[0] = replacement_word
        if phrase_data[1] and phrase_data[1] in replacements2:
            replacement2_word = replacements2[phrase_data[1]]
            print("Replacing \"" + phrase_data[1] + "\" with \"" + replacement2_word + "\"")
            phrase_data[1] = replacement2_word

        response = " ".join(phrase_data)
    else:
        response = raw_phrase

    api.send_reply(response, channel)

def handle_unknown_command(channel):
    api.send_reply("Command not recognized. Try `@stokebot help`", channel)

def handle_delete(command, channel, message_data):
    # Extract just the word from the command
    #word_id = command[len([command_text for command_text in DELETE_COMMAND if command.startswith(command_text)][0]):].strip()
    word_id = command[7:]

    if api.is_admin(message_data['user']):
        definition = dao.get_by_id(word_id)
        if not definition:
            api.send_reply("ID " + word_id + " does not exist.", channel)
            return
        defined_words.remove(definition.word)
        dao.delete_by_id(word_id)
        response = "Ok <@" +message_data['user'] + ">, I deleted ID " + word_id + ": \"" + definition.word + "\"."
    else:
        response = "Sorry <@" +message_data['user'] + ">, only admins can delete words currently."

    api.send_reply(response, channel)

def handle_status_inquiry(channel):
    api.send_reply("I'm here!", channel)

def handle_verbose(command, channel):
    # Extract just the word from the command
    #word = command[len([command_text for command_text in VERBOSE_COMMAND if command.startswith(command_text)][0]):].strip()
    word = command[8:]

    # Read the definition from the database
    definitions = dao.read_definition(word)

    # If no definitions present
    if not definitions:
        api.send_reply("No definitions present for \"" + word + "\"", channel)
        return

    # Reply definitions from the database
    for definition in definitions:
        print(definition)
        api.send_reply(str(definition), channel)


def handle_show_all(channel):
    #definitions = dao.select_all()

    # Reply definitions from the database
    #reply_definitions(definitions, channel)

    api.send_reply("Disabled until a better way of displaying all definitions is implemented (there's too dang many, people!)", channel)

def listen_for_text(slack_rtm_output):
    """
    	Listen for messages sent by certian users. If the message was
    	sent by one of those users, then do more.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            #if output and 'text' in output and 'user' in output and at_target_user_id in output['user']:
            # If there is text present, but that text isnt from this bot,
            if output and 'text' in output and 'user' in output and output['user'] != at_bot_id:
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

    # If no definitions present
    if not definitions:
        api.send_reply("No definitions present for \"" + sanitized_word + "\"", channel)
        return

    # Reply definitions from the database
    reply_definitions(definitions, channel)

def handle_means(command, channel, message_data):
    command_data = command.split(MEANS_COMMAND);
    x = command_data[0].strip()
    y = command_data[1].strip()
    api.send_reply("x: " + str(x) + " MEANS y: " + str(y), channel)
#    command_data = command.split(" ")

#    word = command_data[0]
#    meaning = " ".join(command_data[2:])

#    add_definition(word, meaning, channel, message_data)

def handle_is(command, channel, message_data):
    command_data = command.split(IS_COMMAND)
    x = command_data[0].strip()
    y = command_data[1].strip()
    api.send_reply("x: " + str(x) + " IS y: " + str(y), channel)

def handle_are(command, channel, message_data):
    command_data = command.split(ARE_COMMAND)
    x = command_data[0].strip()
    y = command_data[1].strip()
    api.send_reply("x: " + str(x) + " ARE y: " + str(y), channel)

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
    defined_words.append(word)
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
    blacklisted_words.append(word)
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
    blacklisted_words.remove(blacklisted.word)

    api.send_reply("Ok <@" + message_data['user'] + ">, I've removed " + blacklisted.word + " from the blacklist", channel)

def blacklist_showall(channel):
    blacklist = dao.select_all_blacklisted()

    for blacklisted in blacklist:
        print(str(blacklisted))
        api.send_reply(str(blacklisted), channel)

def reply_definitions(definitions, channel):
    for definition in definitions:
        print("sending " + str(definition) + " to " + channel)
        api.send_reply(("*" + definition.word + "* means _" + definition.meaning + "_"), channel)

def handle_ignore(command, channel, message_data):
    user_name = command[7:]
    user_id = ""

    if user_name == "me":
        user_name = api.get_user_name(message_data['user'])
    elif user_name.startswith("<@"):
        user_id = user_name[2:-1].upper()
        user_name = api.get_user_name(user_id)

    if not user_id:
        user_id = api.get_user_id(user_name)

    channel_name = api.get_name_from_id(message_data['channel'])

    if not (user_id and user_name):
        api.send_reply("Sorry <@" + message_data['user'] + ">, I couldn't find user \"" + command[7:] + "\"", channel)
        return

    user_object = user_model.User()
    user_object.new(user_id, user_name, channel_name)

    reply = ("Ok <@" + message_data['user'] + ">, I will ignore " + ("you" if message_data['user'] == user_id else "<@" + user_name + ">") + " (except commands)")

    if user_id not in ignored_users:
        dao.insert_ignored_user(user_object)
        ignored_users.append(user_id)
    else:
        print("user already in ignored_users, ignoring...")

    api.send_reply(reply, channel)

    print("new ignored_users: " + str(ignored_users))

def handle_listen(command, channel, message_data):
    user_name = command[10:]
    user_id = ""

    if user_name == "me":
        user_name = api.get_user_name(message_data['user'])
    elif user_name.startswith("<@"):
        user_id = user_name[2:-1].upper()
        user_name = api.get_user_name(user_id)

    if not user_id:
        user_id = api.get_user_id(user_name)

    if not (user_id and user_name):
        api.send_reply("Sorry <@" + message_data['user'] + ">, I couldn't find user \"" + command[10:] + "\"", channel)
        return

    reply = ("Ok <@" + message_data['user'] + ">, I will listen to " + ("you" if message_data['user'] == user_id else "<@" + user_name + ">"))

    if user_id in ignored_users:
        dao.delete_ignored_by_user_id(user_id)
        ignored_users.remove(user_id)
    else:
        print("user not in ignored_users, ignoring...")

    api.send_reply(reply, channel)

    print("new ignored_users: " + str(ignored_users))

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = .5 # .5 second delay between reading from firehose
    run = True
    while run:
        try:
            if slack_client.rtm_connect():
                print("StokeBot connected and running!")
                global at_bot_id
                global at_target_user_id
                global defined_words
                global blacklisted_words
                global ignored_users
                at_bot_id = api.get_user_id(BOT_NAME) # Get the bot's ID
                at_target_user_id = api.get_user_id(TARGET_USER_NAME) # Get the target user's ID
                defined_words = dao.get_defined_words()
                blacklisted_words = dao.get_blacklisted_words()
                ignored_users = dao.get_ignored_user_ids()
                print("Got all defined words: " + str(defined_words))
                print("Got all blacklisted words: " + str(blacklisted_words))
                print("Got all blacklisted users: " + str(ignored_users))

                while run:
                    text, channel, message_data = listen_for_text(slack_client.rtm_read())
                    if text and channel:
                        run = handle_text(text, channel, message_data)
                        if not run:
                            api.send_reply(":broken_heart:", channel)
                    time.sleep(READ_WEBSOCKET_DELAY)
            else:
                print("Connection failed. Invalid Slack token or Bot ID?")

        except (KeyboardInterrupt, SystemExit):
            print ("Stopping...")
            quit()
        except Exception as e:
            print ("Encountered error: " + str(e))

        time.sleep(CONNECTION_ATTEMPT_RETRY_DELAY)
