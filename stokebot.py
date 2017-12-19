import os
import time
import definition_model
import blacklist
import ignored
import item
import dao
import api
import word_check
import re
import traceback
import random
from slackclient import SlackClient

# constants
BOT_NAME = os.environ.get('BOT_NAME')#"stokebot"
BOT_OWNER_NAME = os.environ.get('BOT_OWNER_NAME')#"mkwarman"
TARGET_USER_NAME = os.environ.get('TARGET_USER_NAME')#"austoke"
READ_WEBSOCKET_DELAY = .5 # .5 second delay between reading from firehose
CONNECTION_ATTEMPT_RETRY_DELAY = 1
MAX_HELD_ITEMS = 5
POSSESSIVE_DENOTION = "<possessive>"
REPLY_DENOTION = "<reply>"
ACTION_DENOTION = "<action>"
TESTING_CHANNEL_IDS = ("G3RLY44JE", "G3PLLCBB4", "C7XV04PK4")

AT_BOT_ID = api.get_user_id(BOT_NAME) # Get the bot's ID
BOT_MATCH = ("<@" + AT_BOT_ID + ">")
ALT_BOT_MATCH = ("<@" + AT_BOT_ID + "|" + BOT_NAME + ">")
AT_TARGET_USER_ID = api.get_user_id(TARGET_USER_NAME) # Get the target user's ID
AT_BOT_OWNER_ID = api.get_user_id(BOT_OWNER_NAME) # Get the target user's ID

# Chances
DADJOKE_CHANCE = 50

# Triggers
POSSESSIVE_TRIGGERS = ("’s","'s")
REPLY_TRIGGER = ("reply")
ACTION_TRIGGER = ("action")
MEANS_TRIGGER = (" means ")
IS_TRIGGER = (" is ")
ARE_TRIGGER = (" are ")
GIVES_TRIGGER = ("gives")
TAKES_TRIGGER = ("takes")

# Commands
ADD_COMMAND = ("add")
MEANS_COMMAND = ("means")
IS_COMMAND = ("is")
ARE_COMMAND = ("are")
READ_COMMAND = ("what is", "define")
LIST_ITEMS_COMMAND = ("list items")
BLACKLIST_COMMAND = ("blacklist")
VERBOSE_COMMAND = ("verbose")
KARMA_COMMAND = ("karma")
STATUS_COMMAND = ("status")
#SHOW_ALL_COMMAND = ("showall", "show all", "show all definitions", "show all words")
DELETE_COMMAND = ("delete")
STOP_COMMAND = ("stop")
SAY_COMMAND = ("say")
HELP_COMMAND = ("help")
IGNORE_COMMAND = ("ignore")
LISTEN_COMMAND = ("listen to")
CHECK_COMMAND = ("check")

# Matches to check for when explicit relation is detected
POSSESSIVE_MATCH = ("'s")
REPLY_MATCH = ("reply")
ACTION_MATCH = ("action")
MAX_KARMA_CHANGE = 10
TOP_KARMA_SUBCOMMAND = "top"
TOP_KARMA_LIMIT = 5

# globals
global defined_words
global defined_phrases
global blacklisted_words
global ignored_users
global held_items

# Regexs
ITEM_REGEX = re.compile(r'(?i)^(gives|takes) (?:(.+)(?: (?:from|to) (?:' + re.escape(BOT_MATCH) + "|" + re.escape(ALT_BOT_MATCH) + '))|(?:' + re.escape(BOT_MATCH) + "|" + re.escape(ALT_BOT_MATCH) + ') (.+))$')
KARMA_REGEX = re.compile(r'((?:<(?:@|#)[^ ]+>)|\w+) ?(\+\++|--+)')
DADJOKE_REGEX = re.compile(r'(?i)^i[\'\’]m ((?: ?[a-zA-z]+){0,5}) ?$')
TAG_CHECK = re.compile(r'(<(?:@|#)[^ ]+>)')

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_text(text, channel, message_data):
    print("Handling text")
    item_operation = ITEM_REGEX.search(text)
    dadjoke_result = DADJOKE_REGEX.search(text)

    # Container operations are singular, so we don't need to look for other matches
    if (item_operation):
        item.handle_item_operation(item_operation, GIVES_TRIGGER, MAX_HELD_ITEMS, held_items, channel, message_data)
    elif (chance(DADJOKE_CHANCE) and dadjoke_result):
        api.send_reply("Hi \"" + dadjoke_result.group(1) + "\", I'm DadBot!", channel)
    elif (text.startswith(BOT_MATCH) and not re.search('^ ?(--|\+\+)', text[len(BOT_MATCH):])):
        print("Received command: " + text)
        return handle_command(text, channel, message_data)
    elif 'user' in message_data and message_data['user'] not in ignored_users:
        check_user_text(text, channel, message_data, False)

    return True

def check_user_text(text, channel, message_data, testing_mode):
    print("Checking user text")
    print_if_testing("About to sanitize and split:\n" + text, message_data)
    words = word_check.sanitize_and_split_words(text)
    print_if_testing("Got words: " + str(words), message_data)
    unique_words = set(words)

    # Check for karma changes
    karma = KARMA_REGEX.findall(text)
    for result in karma:
        handle_karma_change(result, channel, message_data)

    # Check for defined words
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

    # Check for defined phrases
    for phrase in defined_phrases:
        if phrase in text:
            if testing_mode:
                api.send_reply("Found \"" + phrase + "\" in defined_phrases", channel)
            print("Found\"" + phrase + "\" in defined_phrases")
            definitions = dao.read_definition(phrase)
            dao.increment_word_usage_count(phrase, 1)
            reply_definitions(definitions, channel)

    # Check for target user
    if ('user' in message_data and AT_TARGET_USER_ID in message_data['user']) or testing_mode:
        print_if_testing("Target user said: " + text, message_data)
        handle_target_user_text(unique_words, channel, message_data, testing_mode)

def handle_target_user_text(words, channel, message_data, testing_mode):
    unknown_words = word_check.find_unknown_words(words)
    print_if_testing("Found unknown words: " + str(unknown_words), message_data)
    for word in unknown_words:
        print("About to check_dictionary for \"" + word + "\"")
        if not word_check.check_dictionary(word):
            # definition was not found
            response = "Hey <@" +message_data['user'] + ">! What does \"" + word + "\" mean?"
            api.send_reply(response, AT_TARGET_USER_ID)
            api.send_reply(response, AT_BOT_OWNER_ID)
        else:
            # Insert dictionary word into the blacklist so we dont keep using database queries
            if testing_mode:
                api.send_reply("Found dictionary definition for \"" + word + "\". Adding to blacklist...", channel)
            print("Found dictionary definition for \"" + word + "\". Adding to blacklist...")
            blacklist.blacklist_add_from_dictionary(word, message_data, blacklisted_words)

#Find out why we're getting unknown command
def handle_command(text, channel, message_data):
    print("In handle_command")
    command = text.split(BOT_MATCH)[1].strip().lower()
    print("Parsed command: " + command)

    relation = check_for_explicit_relation(command)

    if relation:
        handle_explicit_relation(command, channel, message_data, relation)
    elif command == STOP_COMMAND:
        return False
    elif command.startswith(ADD_COMMAND):
        handle_add_definition(command, channel, message_data)
    elif command.startswith(READ_COMMAND):
        handle_read_definition(command, channel, message_data)
    elif command.startswith(STATUS_COMMAND):
        handle_status_inquiry(channel)
    elif MEANS_TRIGGER in command:
        handle_multi(command, channel, message_data, MEANS_COMMAND)
    elif IS_TRIGGER in command:
        handle_multi(command, channel, message_data, IS_COMMAND)
    elif ARE_TRIGGER in command:
        handle_multi(command, channel, message_data, ARE_COMMAND)
#    elif command in SHOW_ALL_COMMAND:
#        handle_show_all(channel)
    elif command == LIST_ITEMS_COMMAND:
        item.list_items(held_items, channel)
    elif command.startswith(VERBOSE_COMMAND):
        handle_verbose(command, channel)
    elif command.startswith(KARMA_COMMAND):
        handle_karma(command, channel)
    elif command.startswith(DELETE_COMMAND):
        handle_delete(command, channel, message_data)
    elif command.startswith(IGNORE_COMMAND):
        ignored.handle_ignore(command, channel, message_data, ignored_users)
    elif command.startswith(LISTEN_COMMAND):
        ignored.handle_listen(command, channel, message_data, ignored_users)
    elif command.startswith(SAY_COMMAND):
        handle_say(text, channel, message_data)
    elif command.startswith(BLACKLIST_COMMAND):
        blacklist.handle_blacklist(command, channel, message_data, blacklisted_words)
    elif command.startswith(CHECK_COMMAND):
        handle_check(command, channel, message_data)
    elif command == HELP_COMMAND:
        handle_help(channel)
    else:
        handle_unknown_command(channel)

    return True

def chance(percentage):
    return (random.randint(1, 100) <= percentage) 

def check_for_explicit_relation(command):
    #pattern = re.compile("<(([^@#>])+)>")
    pattern = re.compile("&lt;([^@#<>]+)&gt;")
    match = pattern.search(command)
    if not match:
        return False
    else:
        return match.group(0)

def handle_explicit_relation(command, channel, message_data, relation):
    command_data = command.split(relation)
    x = command_data[0].strip()
    y = command_data[1].strip()
    stripped_relation = relation[4:-4]

    if stripped_relation in POSSESSIVE_TRIGGERS:
        relation = POSSESSIVE_DENOTION
    elif stripped_relation == REPLY_TRIGGER:
        relation = REPLY_DENOTION
    elif stripped_relation == ACTION_TRIGGER:
        relation = ACTION_DENOTION
    else:
        relation = stripped_relation

    add_definition(x, relation, y, channel, message_data)

def handle_karma_change(karma, channel, message_data):
    key = karma[0].lower()
    operator = karma[1]
    delta = len(operator) - 1
    response = (to_first_name_if_tag(key)) + "'s karma has "

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
    key = text.split(" ")[1]

    if key == TOP_KARMA_SUBCOMMAND:
        handle_top_karma(channel)
        return

    response = to_first_name_if_tag(key)

    karma = dao.get_karma(key)

    if karma == None:
        response += " has no karma score!"
    else:
        response += "'s karma is " + str(karma)

    api.send_reply(response, channel)

def handle_top_karma(channel):
    response = "Top karma entries:"
    top_karma_entities = dao.get_top_karma(TOP_KARMA_LIMIT)
    for entity in top_karma_entities:
        response += ("\n" + to_real_name_if_tag(entity[0]) + ": " + str(entity[1]))

    api.send_reply(response, channel)

def handle_check(command, channel, message_data):
    text = command[6:]
    check_user_text(text, channel, message_data, True)

def handle_help(channel):
    response = "Basic Commands:\n" \
               + ">`@stokebot X is/are Y` --- Stokebot will reply \"X is/are Y\" when X is triggered\n"\
               + ">`@stokebot X means Y` --- Stokebot will reply \"X means Y\" with definition format when X is triggered\n" \
               + ">`@stokebot X <'s> Y` --- Stokebot will reply \"X's Y\" when X is triggered\n"\
               + ">`@stokebot X <reply> Y` --- Stokebot will reply \"Y\" when X is triggered\n"\
               + ">`@stokebot X <action> Y` --- Stokebot will reply with \"/me Y\" when X is triggered\n"\
               + ">`/me gives/takes [item] to/from @stokebot` --- Stokebot will take from or give you \"item\"\n"\
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
    raw_phrase = text.split(BOT_MATCH)[1].strip()[4:]
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
        remove_word_or_phrase(definition.word)
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

"""
def handle_show_all(channel):
    #definitions = dao.select_all()

    # Reply definitions from the database
    #reply_definitions(definitions, channel)

    api.send_reply("Disabled until a better way of displaying all definitions is implemented (there's too dang many, people!)", channel)
"""

def listen_for_text(slack_rtm_output):
    """
    	Listen for messages sent by certian users. If the message was
    	sent by one of those users, then do more.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            #if output and 'text' in output and 'user' in output and AT_TARGET_USER_ID in output['user']:
            # If there is text present, but that text isnt from this bot,
            if output and 'text' in output and 'user' in output and output['user'] != AT_BOT_ID:
                return output['text'], output['channel'], output
                # return None, None
    return None, None, None

def handle_read_definition(command, channel, message_data):
    # Extract just the relevent section from the text
    #command = text.split("<@" + AT_BOT_ID + ">")[1].strip()

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

def handle_secondary_add_definition(command, channel, message_data):
    #command = text.split("<@" + AT_BOT_ID + ">")[1].strip()
    command_data = command.split(" ")

def handle_multi(command, channel, message_data, command_root):
    command_data = command.split(command_root)
    x = command_data[0].strip()
    y = command_data[1].strip()

    add_definition(x, command_root, y, channel, message_data)


def handle_add_definition(command, channel, message_data):
    # Extract just the relevent section from the text
    #command = text.split("<@" + AT_BOT_ID + ">")[1].strip()

    # Extract just the word and the meaning from the command
    #word_and_meaning = command[len([command_text for command_text in ADD_COMMAND if command.startswith(command_text)][0]):].split(":")
    word_and_meaning = command[3:].split(":")
    word = word_and_meaning[0].strip()
    meaning = word_and_meaning[1].strip()
    relation = 'means'

    add_definition(word, relation, meaning, channel, message_data)

def add_definition(word, relation, meaning, channel, message_data):
    # Instantiate definition object
    definition_object = definition_model.Definition()

    # Get friendly names of user and channel
    user_name = api.get_user_name(message_data['user'])
    channel_name = api.get_name_from_id(message_data['channel'])

    # Populate definition object
    add_word_or_phrase(word)
    definition_object.new(word, relation, meaning, user_name, channel_name)

    api.send_reply("Ok <@" + message_data['user'] + ">, I'll remember that " + word + " " + relation + " " + meaning, channel)
    print("attempting to insert into database: " + str(definition_object))

    # Send definition object to database
    dao.insert_definition(definition_object)

def reply_definitions(definitions, channel):
    index = 0

    if len(definitions) > 1:
        print("getting random index, max: " + str(len(definitions)))
        index = random.randint(0, len(definitions) - 1)
    
    print("Index: " + str(index))

    definition = definitions[index]

    #for definition in definitions:
    print("sending " + str(definition) + " to " + channel)
    if "<" in definition.relation:
        response = handle_special_relation(definition)
    elif (definition.relation == MEANS_COMMAND):
        # Add definition formatting
        response = ("*" + definition.word + "* " + definition.relation + " _" + definition.meaning + "_")
    else:
        response = (definition.word + " " + definition.relation + " " + definition.meaning)

    api.send_reply(response, channel)

def handle_special_relation(definition):
    print("Found special relation: " + definition.relation)
    if definition.relation == POSSESSIVE_DENOTION:
        # Given: X | Reply: X's Y
        return (definition.word + "'s " + definition.meaning)
    elif definition.relation == REPLY_DENOTION:
        # Given: X | Reply: Y
        return definition.meaning
    elif definition.relation == ACTION_DENOTION:
        # Given: X | Reply: /me Y
        #api.send_command("/me", definition.meaning, channel)
        return ("_" + definition.meaning + "_")
    else:
        # Given: X | Reply: X [relation] Y
        return (definition.word + " " + definition.relation[1:-1] + " " + definition.meaning)

def to_upper_if_tag(text):
    search_result = TAG_CHECK.search(text)

    if search_result:
        tag = search_result.group(1)
        text = text.replace(tag, tag.upper())

    return text

def to_real_name_if_tag(text):
    search_result = TAG_CHECK.search(text)

    if search_result:
        tag = search_result.group(1)
        user_id = tag[2:-1].upper()
        name = api.get_user_real_name(user_id)
        if not name:
            name = tag.upper()
        text = text.replace(tag, name)

    return text

def to_first_name_if_tag(text):
    search_result = TAG_CHECK.search(text)

    if search_result:
        tag = search_result.group(1)
        user_id = tag[2:-1].upper()
        name = api.get_user_first_name(user_id)
        if name:
            text = text.replace(tag, name)
        else:
            print("api.get_user_first_name returned None, checking for real_name instead")
            text = to_real_name_if_tag(text).split(" ")[0]

    return text

def print_if_testing(print_text, message_data):
    if (message_data['channel'] in TESTING_CHANNEL_IDS):
        print(print_text)

def add_word_or_phrase(value):
    if " " not in value:
        defined_words.append(value)
    else:
        defined_phrases.append(value)

def remove_word_or_phrase(value):
    if " " not in value:
        defined_words.remove(value)
    else:
        defined_phrases.remove(value)

def load_data():
    global defined_words
    global defined_phrases
    global blacklisted_words
    global ignored_users
    global testing_channel_ids
    
    defined_words = []
    defined_phrases = []
    
    defined = dao.get_defined_words()
    for value in defined:
        add_word_or_phrase(value)
    
    blacklisted_words = dao.get_blacklisted_words()
    ignored_users = dao.get_ignored_user_ids()
    held_items = dao.get_items()

    print("Got all defined words: " + str(defined_words))
    print("Got all defined phrases: " + str(defined_phrases))
    print("Got all blacklisted words: " + str(blacklisted_words))
    print("Got all blacklisted users: " + str(ignored_users))
    print("Got all held items: " + str(held_items))

if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = .5 # .5 second delay between reading from firehose
    run = True
    while run:
        try:
            if slack_client.rtm_connect():
                print ("Stokebot up and running!")

                load_data()

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
            print ("Encountered error: " + str(e) + "\nTraceback:\n" + traceback.format_exc())

        time.sleep(CONNECTION_ATTEMPT_RETRY_DELAY)
