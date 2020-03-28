import os
import definition.constants
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from functools import reduce
from core import builders, featurebase, helpers
from definition.dao import get_definition_by_trigger, \
                           get_all_definitions_by_trigger, \
                           insert_definition, \
                           get_triggers, \
                           check_trigger, \
                           delete_definition_by_id, \
                           delete_definition_by_trigger, \
                           increment_word_usage, \
                           check_blacklist, \
                           insert_blacklist, \
                           remove_blacklist, \
                           check_ignored, \
                           insert_ignored, \
                           remove_ignored
from definition.sqlalchemy_declarative import Base
from definition.word_check import sanitize_and_split_words, \
        find_unknown_words, find_reactions, check_dictionary
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

# Maximum reactions to allow for one trigger
MAX_TRIGGER_REACTIONS = 10

# Maximum total reactions to attempt to apply to one message with
#   potentially multiple triggers
MAX_TOTAL_REACTIONS = 23


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
        reactions = find_reactions(response)
        if reactions and MAX_TRIGGER_REACTIONS < len(reactions):
            helpers.post_reply(payload,
                               "Wow that's a lot of emoji! " +
                               "You'll need to keep it under " +
                               str(MAX_TRIGGER_REACTIONS) + ", please.",
                               reply_in_thread=True)
            return
        response = ','.join(reactions)

        # TODO: Handle max reactions
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


def handle_triggers(text, distinct_words, known_triggers, payload):
    # We will lazily initialize the session since most messages won't contain
    #   triggers
    session = None

    reply_responses, action_responses, react_responses, means_responses, \
        is_responses = [], [], [], [], []

    for trigger in known_triggers:
        '''
        If the current trigger is a phrase trigger (contains spaces) then
          check to see if it exists anywhere in the text as presented.
        If the current trigger is a single word trigger then check to see
          if it exists in the distinct set of sanitized and split words
          from the text
        '''
        if trigger in (text if " " in trigger else distinct_words):
            # Prints what trigger was found in which string/set above
            # print("check if " + trigger + " in " + (text if " " in
            #       trigger else str(distinct_words)))
            if not session:
                # Initialize the session if it hasnt been already
                session = DBSession()
            found_def = get_definition_by_trigger(session, trigger)

            if not found_def:
                # This shouldnt happen
                print("Received falsy definition relation from dao!")
                return

            increment_word_usage(session, trigger)
            def_relation = __get_relation_from_enum(RelationEnum(
                found_def.relation))

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

    # DM the target user to ask for a definition. Do not reply in thread
    helpers.dm_reply(payload, message, False)


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
    all_results = get_all_definitions_by_trigger(session, command.lower())
    session.close()

    if not all_results or 1 > len(all_results):
        reply = "Hmm, I don't know any definitions for {0}".format(command)
        helpers.post_reply(payload, reply, reply_in_thread=True)
        return

    reply = "I know the following definitions for {0}:".format(command)

    for result in all_results:
        reply += "\n({0}) {1}{2}{3}".format(
                result.id,
                result.trigger,
                __get_relation_from_enum(result.relation),
                result.response)

    helpers.post_reply(payload, reply, reply_in_thread=True)


def handle_delete_definition(command, payload):
    def_id = None
    try:
        def_id = int(command.strip())
    except ValueError:
        pass

    if def_id:
        # If def_id was an integer ID of a trigger
        __delete_definition_by_id(def_id, command, payload)
    else:
        # If def_id wasn't an integer, maybe it is the trigger itself
        __delete_definition_by_trigger(command, payload)


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
    relationEnum = None
    try:
        relationEnum = RelationEnum(relation)
    except (ValueError):
        print("WARN: Encountered unknown relation: " + str(relation))

    if relationEnum == RelationEnum.REPLY:
        return REPLY_RELATION
    elif relationEnum == RelationEnum.ACTION:
        return ACTION_RELATION
    elif relationEnum == RelationEnum.REACT:
        return REACT_RELATION
    elif relationEnum == RelationEnum.MEANS:
        return MEANS_RELATION
    return IS_RELATION


def __handle_react_responses(responses, payload):
    if len(responses) < 1:
        return

    all_reactions = reduce(lambda x, y: x+','+y, responses)

    seen = set()
    distinct_reactions = [x for x in all_reactions.split(',')
                          if x not in seen and not seen.add(x)]

    if MAX_TOTAL_REACTIONS < len(distinct_reactions):
        distinct_reactions = distinct_reactions[:MAX_TOTAL_REACTIONS]

    for reaction in distinct_reactions:
        helpers.react_reply(payload, reaction)


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


def __delete_definition_by_id(def_id, command, payload):
    session = DBSession()
    delete_successful = delete_definition_by_id(session, def_id)
    session.close()

    # Reply inside thread
    if delete_successful:
        helpers.post_reply(
                payload, "Ok, I deleted definition ID " + command, True)
        return


def __delete_definition_by_trigger(command, payload):
    reply = ""
    session = DBSession()
    all_results = get_all_definitions_by_trigger(session, command.lower())

    if not all_results or 1 > len(all_results):
        # No definitions found
        reply = "I'm sorry, I couldnt find a matching definition",
    if 1 < len(all_results):
        # Multiple definitions found
        reply = "I know the following definitions for {0}:".format(command)
        for result in all_results:
            reply += "\n({0}) {1}{2}{3}".format(
                    result.id,
                    result.trigger,
                    __get_relation_from_enum(result.relation),
                    result.response)
    else:
        # One definition found
        delete_definition_by_trigger(session, command.lower())
        reply = "Ok, I deleted the definition for " + command

    session.close()
    helpers.post_reply(payload, reply, reply_in_thread=True)


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

        # Sanitize and split words, put them in a set to remove duplicates
        distinct_words = set(sanitize_and_split_words(text))

        # Check to see if there are any triggers in the text
        handle_triggers(text, distinct_words, self.triggers, payload)

        if user in os.getenv('DEFINITION_TARGET_USER_ID').split(','):
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
                if new_definition:
                    # Only add the new trigger if we were actually
                    #   able to add the new definition
                    self.triggers.add(new_definition)
                return True

        return False

    def get_help(self):
        bb = builders.BlocksBuilder()
        sb = builders.SectionBuilder()
        sb.add_text("*Adding Definitions:*\n")  # noqa: E501
        sb.add_text("When you say: <@{botid}> _trigger_{is_relation}_response_\n")  # noqa: E501
        sb.add_text("    • {botname} will reply: \"trigger is response\"\n")  # noqa: E501
        sb.add_text("When you say: <@{botid}> _trigger_{means_relation}_response_\n")  # noqa: E501
        sb.add_text("    • {botname} will reply: \"*trigger* means _response_\"\n")  # noqa: E501
        sb.add_text("When you say: <@{botid}> _trigger_{react_relation}_emojiname_\n")  # noqa: E501
        sb.add_text("    • {botname} will react to the trigger message with the specified emoji\n")  # noqa: E501
        sb.add_text("When you say: <@{botid}> _trigger_{reply_relation}_response_\n")  # noqa: E501
        sb.add_text("    • {botname} will reply: \"response\"\n")  # noqa: E501
        sb.add_text("When you say: <@{botid}> _trigger_{action_relation}_response_\n")  # noqa: E501
        sb.add_text("    • {botname} will reply: \"_response_\", similar to when someone uses the '/me' command\n")  # noqa: E501
        sb.format_text(botid=os.getenv('BOT_ID'),
                       botname=os.getenv('BOT_NAME'),
                       is_relation=IS_RELATION,
                       means_relation=MEANS_RELATION,
                       react_relation=REACT_RELATION,
                       reply_relation=REPLY_RELATION,
                       action_relation=ACTION_RELATION
                       )
        bb.add_block(sb.section)
        bb.add_divider()

        sb.add_text("\n*Setting Ignore:*\n")  # noqa: E501
        sb.add_text("To make {botname} stop responding to your messages (except direct commands):\n")  # noqa: E501
        sb.add_text("    • <@{botid}> ignore me\n")  # noqa: E501
        sb.add_text("To make {botname} listen to you again:\n")  # noqa: E501
        sb.add_text("    • <@{botid}> listen to me\n")  # noqa: E501
        sb.format_text(botid=os.getenv('BOT_ID'),
                       botname=os.getenv('BOT_NAME')
                       )
        bb.add_block(sb.section)
        bb.add_divider()

        sb.add_text("\n*Managing Definitions:*\n")  # noqa: E501
        sb.add_text("Show Responses for a trigger:\n")  # noqa: E501
        sb.add_text("    • <@{botid}> definition list _trigger_\n")  # noqa: E501
        sb.add_text("Delete a trigger using ID from `definition list trigger`:\n")  # noqa: E501
        sb.add_text("    • <@{botid}> definition [remove, delete] _triggerid_\n")  # noqa: E501
        sb.format_text(botid=os.getenv('BOT_ID'))
        bb.add_block(sb.section)
        bb.add_divider()

        sb.add_text("\n*Managing Blacklist:*\n")  # noqa: E501
        sb.add_text("Add a trigger to the blacklist:\n")  # noqa: E501
        sb.add_text("    • <@{botid}> blacklist add _trigger_\n")  # noqa: E501
        sb.add_text("Delete a trigger from the blacklist:\n")  # noqa: E501
        sb.add_text("    • <@{botid}> blacklist [remove, delete] _trigger_\n")  # noqa: E501
        sb.format_text(botid=os.getenv('BOT_ID'))
        bb.add_block(sb.section)

        return bb.blocks


def get_feature_class():
    return Definition()
