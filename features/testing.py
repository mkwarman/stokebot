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
    def on_message(self, text, data, client):
        say_hello(data, client)

    def on_command(self, command, data, client):
        if (command.lower() == ("test") or
           command.lower() == ("status")):
            helpers.post_reply(client, data, "I'm here!")
            return True

        if (command.lower() == ("newtest")):
            helpers.post_reply(client, data, "server test active!",
                               override=True)
            return True

        if (command.lower() == ("dm me")):
            helpers.dm_reply(client, data, "Lemme slide into those DMs, fam")
            return True


def get_feature_class():
    return Testing()
