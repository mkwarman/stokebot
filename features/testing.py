import os
from core import helpers, featurebase


# Respond when someone says "Hello @[botname]"
def say_hello(data, web_client):
    trigger_text = ("hello %s" % (os.getenv("BOT_NAME")))
    if 'text' in data and trigger_text in data['text'].lower():
        channel_id = data['channel']
        # channel_id = os.getenv("TEST_CHANNEL_ID")
        thread_ts = data['ts']
        text = "Hi, <@%s>!" % (data['user'])

        helpers.post_thread_message(web_client, channel_id, thread_ts, text)
        # helpers.post_message(web_client, channel_id, text)


class Testing(featurebase.FeatureBase):
    def on_message(self, text, payload):
        data = payload['data']
        web_client = payload['web_client']

        say_hello(data, web_client)

    def on_command(self, command, payload):
        if (command.lower() == ("test") or
           command.lower() == ("status")):
            helpers.post_reply(payload, "I'm here!")
            return True


def get_feature_class():
    return Testing()
