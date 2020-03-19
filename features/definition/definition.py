import os
import definition.constants
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core import helpers, featurebase
from definition.dao import get_definition_by_trigger, \
        get_all_definitions_by_trigger, insert_definition, \
        get_triggers, check_trigger, delete_definition_by_id, \
        increment_word_usage, check_blacklist, insert_blacklist, \
        remove_blacklist, check_ignored, insert_ignored, remove_ignored
from definition.sqlalchemy_declarative import Base
from definition.word_check import sanitize_and_split_words, \
        find_unknown_words, check_dictionary
from definition.relation_enum import RelationEnum

engine = create_engine("sqlite:///data/definition.db")
# Bind the engine to the metadata so we can use the declartives in
#   sqlalchemy_declarative
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# DBSession acts as a staging area facillitating sessions, commits,
#   rollback, etc

REPLY_RELATION = " &lt;reply&gt; "
ACTION_RELATION = " &lt;action&gt; "
REACT_RELATION = " &lt;react&gt; "
MEANS_RELATION = " means "
IS_RELATION = " is "
RELATIONS = [REPLY_RELATION, ACTION_RELATION, REACT_RELATION,
             MEANS_RELATION, IS_RELATION]
VARIABLE_TRIGGER = "$"


def get_known_triggers():
    session = DBSession()
    all_triggers = get_triggers(session) or []
    session.close()

    distinct_triggers = set(all_triggers)
    print('Loaded {0} definitions for {1} triggers'
          .format(len(all_triggers), len(distinct_triggers)))

    return distinct_triggers


def handle_add_definition(command, relation, payload):
    # Extract trigger and response from command.
    # Relation is passed in as identified
    command_lower = command.lower()
    split_command = command.split(
            command[command_lower.index(relation):
                    command_lower.index(relation)+len(relation)],
            1)
    trigger = split_command[0].strip()
    response = split_command[1].strip()
    user = helpers.get_user_from_payload(payload)

    if not (trigger and relation and response):
        return False

    reply_response = response
    if relation == REACT_RELATION:
        # Sanitize emojis since the api expects just their name without colons
        response = response.replace(':', '')
        # TODO: validate react definitions (ensure emoji exists)

    session = DBSession()
    # Get the integer version of the relation before saving it to the database
    insert_definition(session, trigger,
                      __get_enum_from_relation(relation).value, response, user)
    session.close()

    # Get friendly name for user, construct reply and then send it
    user_name = helpers.get_first_name_from_id(user, payload['web_client'])
    reply = "Ok {0}, I'll remember {1}{2}{3}".format(user_name, trigger,
                                                     relation, reply_response)
    helpers.post_reply(payload, reply)

    return trigger


def handle_triggers(text, known_triggers, payload):
    # We will lazily initialize the session since most messages won't contain
    #   triggers
    session = None

    reply_responses, action_responses, react_responses, means_responses, \
        is_responses = [], [], [], [], []

    for trigger in known_triggers:
        if trigger in text:
            if not session:
                # Initialize the session if it hasnt been already
                session = DBSession()
            found_def = get_definition_by_trigger(session, trigger)
            increment_word_usage(session, trigger)
            def_relation = __get_relation_from_enum(RelationEnum(
                found_def.relation))

            if not found_def:
                # This shouldnt happen
                print("Received falsy definition relation from dao!")

            # reply_responses
            if def_relation == REPLY_RELATION:
                reply_responses.append(found_def.response)
            # action_responses
            elif def_relation == ACTION_RELATION:
                action_responses.append(found_def.response)
            # reaction_responses
            elif def_relation == REACT_RELATION:
                react_responses.append(
                        __check_for_variables(found_def.response))
            # means_responses
            elif def_relation == MEANS_RELATION:
                means_responses.append((found_def.trigger, found_def.response))
            # is_responses
            elif def_relation == IS_RELATION:
                is_responses.append((found_def.trigger, found_def.response))
            else:
                # this shouldnt happen
                return

    if session:
        # Close the session if we ended up initializing it
        session.close()

    # Handle all the various found triggers
    __handle_react_responses(react_responses, payload)
    __handle_action_responses(action_responses, payload)
    __handle_reply_responses(reply_responses, payload)
    __handle_means_responses(means_responses, payload)
    __handle_is_responses(is_responses, payload)

    # TODO: Consider sorting replies to correspond with trigger location
    #   in original message


def handle_unknown_words(unknown_words, user, payload):
    session = DBSession()

    words_to_define = []
    for word in unknown_words:
        # Check for unknown word in blacklist
        found = check_blacklist(session, word)
        if found:
            return
        # Check for unknown word in triggers
        found = check_trigger(session, word)
        if found:
            return
        # Check for unknown word in dictionary
        found = check_dictionary(word)
        if found:
            insert_blacklist(session, word, 'dictionary')
            return
        words_to_define.append(word)

    session.close()

    if (len(words_to_define) > 0):
        ask_for_definitions(words_to_define, user, payload)


def ask_for_definitions(words_to_define, user, payload):
    message = "Hey <@{0}>, what ".format(user)

    # For multiple words, ask for all of their definitions at once.
    # Otherwise just as for one
    if (len(words_to_define) == 1):
        message += "does \"{0}\" mean?".format(words_to_define[0])
    elif (len(words_to_define) > 1):
        message += "do the following words mean?"
        for word in words_to_define:
            message += "\n>{0}".format(word)
    else:
        # This shouldn't happen, but handle it if it does
        return

    helpers.post_message(payload['web_client'], os.getenv('TEST_CHANNEL_ID'),
                         message)


def handle_ignore(should_ignore, payload):
    user = helpers.get_user_from_payload(payload)

    if not user:
        # If this is not a person then just return
        return

    session = DBSession()
    reply = "Ok, {0}, I will ".format(helpers.get_first_name_from_id(
        user, payload['web_client']))

    if should_ignore:
        insert_ignored(session, user)
        reply += "stop "
    else:
        remove_ignored(session, user)
        reply += "resume "

    session.close()
    reply += "listening to you."
    helpers.post_reply(payload, reply)


def handle_blacklist(should_blacklist, trigger, payload):
    user = helpers.get_user_from_payload(payload)

    if not user:
        # If this is not a person then just return
        return

    session = DBSession()
    reply = "Ok, {0}, I will ".format(helpers.get_first_name_from_id(
        user, payload['web_client']))

    if should_blacklist:
        insert_blacklist(session, trigger, user)
        reply += "add {0} to ".format(trigger)
    else:
        remove_blacklist(session, trigger)
        reply += "remove {0} from ".format(trigger)

    session.close()
    reply += "the blacklist."
    helpers.post_reply(payload, reply)


def handle_list_definition(command, payload):
    session = DBSession()
    all_results = get_all_definitions_by_trigger(session, command)
    session.close()

    reply = "I know the following definitions for {0}:".format(command)

    for result in all_results:
        reply += "\n({0}) {1}{2}{3}".format(
                result.id,
                result.trigger,
                __get_relation_from_enum(result.relation),
                result.response)

    # Reply with definition information inside a thread
    helpers.post_reply(payload, reply, True)


def handle_delete_definition(command, payload):
    def_id = None
    try:
        def_id = int(command.strip())
    except ValueError:
        helpers.post_reply(
                payload,
                "I'm sorry, I couldnt find a definition with that ID",
                True)
        return

    if not def_id:
        helpers.post_reply(
                payload,
                "I'm sorry, I couldnt find a definition with that ID",
                True)
        return

    session = DBSession()
    delete_successful = delete_definition_by_id(session, def_id)
    session.close()

    # Reply inside thread
    if delete_successful:
        helpers.post_reply(
                payload, "Ok, I deleted definition ID " + command, True)
        return

    helpers.post_reply(
            payload,
            "I'm sorry, I couldnt find a definition with that ID", True)


def is_ignored_user(user):
    if not user:
        # If this is not a person then just return
        return

    session = DBSession()
    ignored = check_ignored(session, user)
    session.close()

    return True if ignored else False


def __get_enum_from_relation(relation):
    if relation == REPLY_RELATION:
        return RelationEnum.REPLY
    elif relation == ACTION_RELATION:
        return RelationEnum.ACTION
    elif relation == REACT_RELATION:
        return RelationEnum.REACT
    elif relation == MEANS_RELATION:
        return RelationEnum.MEANS
    return RelationEnum.IS


def __get_relation_from_enum(relation):
    if relation == RelationEnum.REPLY:
        return REPLY_RELATION
    elif relation == RelationEnum.ACTION:
        return ACTION_RELATION
    elif relation == RelationEnum.REACT:
        return REACT_RELATION
    elif relation == RelationEnum.MEANS:
        return MEANS_RELATION
    return IS_RELATION


def __handle_react_responses(responses, payload):
    for response in responses:
        helpers.react_reply(response, payload)


def __handle_action_responses(responses, payload):
    for response in responses:
        helpers.post_reply(payload, "_{0}_".format(response))


def __handle_reply_responses(responses, payload):
    for response in responses:
        helpers.post_reply(payload, "{0}".format(response))


def __handle_means_responses(trigger_response_pairs, payload):
    if len(trigger_response_pairs) < 1:
        return

    reply = ''
    for i, trigger_response_pair in enumerate(trigger_response_pairs):
        if i > 0:
            reply += "\n"
        reply += ("*{0}* means _{1}_".format(
            trigger_response_pair[0], trigger_response_pair[1]))

    helpers.post_reply(payload, reply)


def __handle_is_responses(trigger_response_pairs, payload):
    if len(trigger_response_pairs) < 1:
        return

    reply = ''
    for i, trigger_response_pair in enumerate(trigger_response_pairs):
        if i > 0:
            reply += "\n"
        reply += ("{0} is {1}".format(trigger_response_pair[0],
                                      trigger_response_pair[1]))

    helpers.post_reply(payload, reply)


def __check_for_variables(response):
    # Check for the trigger first since most of the time there won't be one
    if VARIABLE_TRIGGER in response:
        # One of the words might be a variable
        for word in response.split(" "):
            if word.startswith(VARIABLE_TRIGGER):
                dict_key = word[1:]
                if dict_key in definition.constants.VARS_DICT:
                    response = response.replace(
                            (VARIABLE_TRIGGER + dict_key),
                            definition.constants.get_random(dict_key), 1)

    return response


class Definition(featurebase.FeatureBase):
    def __init__(self):
        self.triggers = get_known_triggers()

    def on_message(self, text, payload):
        user = helpers.get_user_from_payload(payload)
        if is_ignored_user(user):
            return

        text = text.lower()

        # Check to see if there are any triggers in the text
        handle_triggers(text, self.triggers, payload)

        if user in os.getenv('DEFINITION_TARGET_USER_ID').split(','):
            # Sanitize and split words, put them in a set to remove duplicates
            distinct_words = set(sanitize_and_split_words(text))

            # Remove known triggers from the set
            for trigger in self.triggers:
                distinct_words.discard(trigger)

            # Find unknown words from those that remain,
            #   and handle them if found
            unknown_words = find_unknown_words(distinct_words)
            if unknown_words:
                handle_unknown_words(unknown_words, user, payload)

    def on_command(self, command, payload):
        lower_command = command.lower()
        if lower_command.startswith("ignore me"):
            handle_ignore(True, payload)
            return True
        elif lower_command.startswith("listen to me"):
            handle_ignore(False, payload)
            return True
        elif lower_command.startswith("blacklist add"):
            handle_blacklist(True, command[14:], payload)
            return True
        elif lower_command.startswith("blacklist remove") \
                or lower_command.startswith("blacklist delete"):
            handle_blacklist(False, command[17:], payload)
            return True
        elif lower_command.startswith("definition remove") \
                or lower_command.startswith("definition delete"):
            handle_delete_definition(command[18:], payload)
            return True
        elif lower_command.startswith("definition list"):
            handle_list_definition(command[16:], payload)
            return True

        for relation in RELATIONS:
            if relation in lower_command:
                new_definition = handle_add_definition(
                        command, relation, payload)
                if not new_definition:
                    # We were unable to add the new definition,
                    #   so something was wrong with the command
                    return False
                self.triggers.add(new_definition)
                return True

        return False


def get_feature_class():
    return Definition()
