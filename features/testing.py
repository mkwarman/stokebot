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
    def slack_connected(self, client):
        self.client = client

    def on_message(self, text, data):
        say_hello(data, self.client)

    def on_command(self, command, data):
        if (command.lower() == ("test") or
           command.lower() == ("status")):
            self.client.post_reply(data, "I'm here!")
            return True

        if (command.lower() == ("newtest")):
            self.client.post_reply(data, "server test active!",
                                   override_silent=True)
            return True

        if (command.lower() == ("dm me")):
            self.client.dm_reply(data,
                                 "Lemme slide into those DMs, fam")
            return True


def get_feature_class():
    return Testing()
