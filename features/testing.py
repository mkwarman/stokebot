import os
# import json
from core import helpers, featurebase, builders


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
    sent_message = None

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

        # These commands are ok for testing, but saving the sent message in
        #   memory is not safe. Different workers will have different 'self's
        if (command.lower() == ("post test message")):
            self.sent_message = self.client.post_reply(data,
                                                       "test message unedited")
            return True

        if (command.lower() == ("edit test message")):
            print("self.sent_message")
            print(self.sent_message)
            if (self.sent_message is not None
               and self.sent_message.get('channel', False)
               and self.sent_message.get('message', False)
               and self.sent_message.get('message').get('ts', False)):
                channel = self.sent_message.get('channel')

                timestamp = self.sent_message.get('message').get('ts')
                self.client.update(channel, timestamp, "test message *edited*")
            else:
                print("didnt find test message")

            return True

        if (command.lower() == ("post interaction message")):
            bb = builders.BlocksBuilder()
            sb = builders.SectionBuilder()
            sb.add_text("This is a test button")
            sb.add_button("Button", "test_value")
            bb.add_block(sb.section)

            self.sent_message = self.client.post_reply(data,
                                                       blocks=bb.blocks)
            return True


def get_feature_class():
    return Testing()
