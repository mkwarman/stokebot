import os
import sys
import pkgutil
import slack
import traceback
import json
from importlib import import_module
from core import helpers, featurebase
from core.builders import BlocksBuilder
from dotenv import load_dotenv

load_dotenv()

BOT_MATCH = "<@{0}>".format(os.getenv("BOT_ID"))
feature_classes = []


# Load all features from features directory, instantiate their associate
#   feature classes, and add them to the feature_classes list
def load_features():
    # Append feature modules directory
    sys.path.append('features')
    import features

    for importer, modname, ispkg in pkgutil.iter_modules(features.__path__):
        print("Going to load {0}'"
              .format(("package '" if ispkg else "module '") + modname))
        feature = import_module(modname)
        if ispkg:
            for name in feature.__all__:
                print("Going to load submodule '{0}' from '{1}'"
                      .format(name, modname))
                subfeature = import_module(modname + "." + name, modname)
                load_feature(subfeature)
        else:
            load_feature(feature)


def load_feature(feature):
    try:
        feature_class = feature.get_feature_class()
        if isinstance(feature_class, featurebase.FeatureBase):
            feature_classes.append(feature_class)
        else:
            raise Exception("feature class does not extend FeatureBase")
    except AttributeError:
        print("Loaded feature without class: {0}".format(feature))
    except Exception as ex:
        print("---> Could not load module: {0}\n---> Because {1}"
              .format(feature, ex))
    else:
        print("Loaded feature: %s" % feature)


def slack_connected(client):
    helpers.post_message(client, os.getenv("PRIVATE_TEST_CHANNEL_ID"),
                         "Hello world!")

    for feature in feature_classes:
        print("telling " + str(feature) + " that we're connected to slack")
        feature.slack_connected(client)


def ready():
    for feature in feature_classes:
        print("telling " + str(feature) + " that we're ready")
        feature.ready()


@slack.RTMClient.run_on(event='message')
def notify_features(**payload):
    try:
        if 'bot_id' in payload['data'] \
                and payload['data']['bot_id'] == os.getenv("APP_ID"):
            # The bot should not talk to itself
            return

        text = helpers.get_text(payload)

        if text is None:
            return

        # '/me' message
        if 'subtype' in payload['data'] \
                and 'me_message' == payload['data']['subtype']:
            for feature in feature_classes:
                feature.on_me_message(text, payload)

        # Command
        if text.startswith(BOT_MATCH) and not (
                ('subtype' in payload['data']
                 and 'group_join' == payload['data']['subtype'])
                or text.startswith(BOT_MATCH + "++")
                or text.startswith(BOT_MATCH + "--")):
            # Remove bot name from the front of the text as well as any
            #   whitespace around it
            command = text[len(BOT_MATCH) + 1:].strip()

            if command == "help":
                __handle_help_command(payload)
                return

            command_matched = False
            for feature in feature_classes:
                command_matched = (command_matched
                                   or feature.on_command(command, payload))

            if not command_matched:
                helpers.post_reply(
                        payload,
                        "I'm sorry, I didnt recognize that command :pensive:")

        # Regular message
        else:
            for feature in feature_classes:
                feature.on_message(text, payload)
    except (KeyboardInterrupt, SystemExit):
        print("Stopping...")
    except Exception as e:
        exception_message = ("Encountered error: " + str(e) +
                             "\nTraceback:\n```\n" +
                             traceback.format_exc() + "```")
        if 'data' in payload:
            exception_message = (exception_message + "\nPayload Data:\n```\n" +
                                 json.dumps(payload['data']) + "\n```")
        print(exception_message)
        helpers.post_message(payload['web_client'],
                             # os.getenv("TEST_CHANNEL_ID"),
                             os.getenv("PRIVATE_TEST_CHANNEL_ID"),
                             exception_message)


def __handle_help_command(payload):
    text = ""

    bb = BlocksBuilder()
    for feature in feature_classes:
        feature_help = feature.get_help()
        if feature_help and len(feature_help) > 0:
            if bb.has_block:
                bb.add_divider()
            bb.add_blocks(feature_help)

    helpers.post_reply(payload, text,
                       blocks=json.dumps(bb.blocks))


if __name__ == "__main__":
    load_features()

    client = slack.WebClient(token=os.getenv("SLACK_TOKEN"))
    slack_connected(client)

    ready()

    rtm_client = slack.RTMClient(token=os.getenv("SLACK_TOKEN"))
    rtm_client.start()
