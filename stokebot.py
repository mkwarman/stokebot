import os
import sys
import pkgutil
import slack
import traceback
import json
import argparse
from importlib import import_module
from core import helpers, featurebase
from core.builders import BlocksBuilder
from core.client import Client
from dotenv import load_dotenv
from flask import Flask, request

application = Flask(__name__)

load_dotenv()

BOT_MATCH = "<@{0}>".format(os.getenv("BOT_ID"))
feature_classes = []
args = None
slack_client = None


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
    client.post_message(os.getenv("PRIVATE_TEST_CHANNEL_ID"),
                        "Hello world!")

    for feature in feature_classes:
        print("telling " + str(feature) + " that we're connected to slack")
        feature.slack_connected(client)


def on_message(data):
    try:
        if ('bot_id' in data
           and data['bot_id'] == os.getenv("APP_ID")):
            # The bot should not talk to itself
            return

        text = helpers.get_text(data)

        if text is None:
            return

        # '/me' message
        if 'subtype' in data \
                and 'me_message' == data['subtype']:
            for feature in feature_classes:
                feature.on_me_message(text, data)

        # Command
        if text.startswith(BOT_MATCH) and not (
                ('subtype' in data
                 and 'group_join' == data['subtype'])
                or text.startswith(BOT_MATCH + "++")
                or text.startswith(BOT_MATCH + "--")):
            # Remove bot name from the front of the text as well as any
            #   whitespace around it
            command = text[len(BOT_MATCH) + 1:].strip()

            if command == "help":
                __handle_help_command(data, client)
                return

            command_matched = False
            for feature in feature_classes:
                command_matched = (command_matched
                                   or feature.on_command(command,
                                                         data))

            if not command_matched:
                client.post_reply(
                       data,
                       "I'm sorry, I didnt recognize that command :pensive:")

        # Regular message
        else:
            for feature in feature_classes:
                feature.on_message(text, data)
    except Exception as e:
        exception_message = ("TEST Encountered error: " + str(e) +
                             "\nTEST Traceback:\n```\n" +
                             traceback.format_exc() + "```" +
                             "\nTEST Payload Data:\n```\n" +
                             json.dumps(data) + "\n```")
        print(exception_message)
        client.post_message(os.getenv("PRIVATE_TEST_CHANNEL_ID"),
                            #  os.getenv("TEST_CHANNEL_ID"),
                            exception_message,
                            override_silent=True)


def __handle_help_command(data, client):
    text = ""

    bb = BlocksBuilder()
    for feature in feature_classes:
        feature_help = feature.get_help()
        if feature_help and len(feature_help) > 0:
            if bb.has_block:
                bb.add_divider()
            bb.add_blocks(feature_help)

    client.post_reply(data, text,
                      blocks=json.dumps(bb.blocks))


@application.route("/slack/event", methods=["POST"])
def message_actions():
    body = request.json

    if ('type' in body
       and "url_verification" == body['type']
       and 'challenge' in body):
        return body['challenge']

    if ('event' in body
       and 'type' in body['event']
       and body['event']['type'] == 'message'):
        on_message(body['event'])

    return "ok"


def load_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--silent', action='store_true',
                        help='Logs actions instead of sending them to slack')
    parser.add_argument('--host',
                        help='Specity host for test server to listen on')
    parser.add_argument('--port',
                        help='Specity port for test server to listen on')
    return parser.parse_args()


def setup():
    global args
    args = load_args()

    load_features()

    if (args.silent):
        print("\n**************** STARTING IN SILENT MODE ****************\n")

    global client
    client = Client(slack.WebClient(token=os.getenv("SLACK_TOKEN")),
                    silent=args.silent)

    slack_connected(client)


setup()

if __name__ == "__main__":
    application.run(host=args.host, port=args.port)
