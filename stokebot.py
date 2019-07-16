import os
import sys
import pkgutil
import slack
from importlib import import_module
from core import helpers, featurebase
from dotenv import load_dotenv

import inspect

load_dotenv()

feature_classes = []

# Load all features from features directory, instantiate their associate feature classes, and add them to the feature_classes list
def load_features():
    # Append feature modules directory
    sys.path.append('features')
    import features

    for importer, modname, ispkg in pkgutil.iter_modules(features.__path__):
        print("Going to load %s'" % (("package '" if ispkg else "module '") + modname))
        feature = import_module(modname)
        if ispkg:
            for name in feature.__all__:
                print("Going to load submodule '%s' from '%s'" % (name, modname))
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
    except AttributeError as ae:
        print("Loaded feature without class: %s" % feature)
    except Exception as ex:
        print("---> Could not load module: %s\n---> Because %s" % (feature, ex))
    else:
        print("Loaded feature: %s" % feature)

def slack_connected(client):
    helpers.post_message(client, os.getenv("TEST_CHANNEL_ID"), "Hello world!")

    for feature in feature_classes:
        print("telling " + str(feature) + " that we're connected to slack")
        feature.slack_connected(client)

def ready():
    for feature in feature_classes:
        print("telling " + str(feature) + " that we're ready")
        feature.ready()

@slack.RTMClient.run_on(event='message')
def notify_features(**payload):
    if 'bot_id' in payload['data'] and payload['data']['bot_id'] == os.getenv("BOT_ID"):
        # The bot should not talk to itself
        return
    
    text = helpers.get_text(payload)

    if text is None:
        return

    for feature in feature_classes:
        feature.on_message(text, payload)

if __name__ == "__main__":
    load_features()

    client = slack.WebClient(token=os.getenv("SLACK_TOKEN"))
    slack_connected(client)

    ready()

    rtm_client = slack.RTMClient(token=os.getenv("SLACK_TOKEN"))
    rtm_client.start()
