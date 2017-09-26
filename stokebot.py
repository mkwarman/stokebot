import os
import time
import definition_model
import dao
import api
from slackclient import SlackClient

# constants
BOT_NAME = "stokebot"
TARGET_USER_NAME = "mkwarman"
EXAMPLE_COMMAND = "do"
ADD_COMMAND = "add"

# globals
global at_bot_id
global at_target_user_id

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_target_user_text(text, channel, message_data):
    print("Handling target user text")
    response = "Target user said: " + text
    print("Sending \"chat.postMessage\":" \
            "\n  channel=\"" + channel + "\"" \
            "\n  text=\"" + response + "\"" \
            "\n  as_user=True")
    print(at_bot_id)
    print(text)
    print(text.split("<@" + at_bot_id + ">")[1].strip().lower())
    if at_bot_id in text and text.split("<@" + at_bot_id + ">")[1].strip().lower().startswith(ADD_COMMAND):
        print("about to handle_add_definition")
        handle_add_definition(text, channel, message_data)
        return
    print("about to respond - unrecognized command: " + text)
    print("at_bot_id: " + at_bot_id)
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def listen_for_user(slack_rtm_output):
    """
    	Listen for messages sent by certian users. If the message was
    	sent by one of those users, then do more.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and 'user' in output and at_target_user_id in output['user']:
                print("Target user said: " + output['text'])
                return output['text'], output['channel'], output
                # return None, None
    return None, None, None

def handle_add_definition(text, channel, message_data):
    command = text.split("<@" + at_bot_id + ">")[1].strip().split(":")
    word = command[0][len(ADD_COMMAND):].strip()
    print("word: " + word)
    definition = command[1].strip()
    print("definition: " + definition)

    definition_object = definition_model.Definition()
    user_name = api.get_user_name(message_data['user'])
    print("user_name: " + user_name)
    print(message_data)
    channel_name = api.get_name_from_id(message_data['channel'])
    print("channel_name: " + channel_name)

    definition_object.new(word, definition, user_name, channel_name)


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StokeBot connected and running!")
        global at_bot_id
        global at_target_user_id
        at_bot_id = api.get_user_id(BOT_NAME) # Get the bot's ID
        at_target_user_id = api.get_user_id(TARGET_USER_NAME) # Get the target user's ID

        while True:
            text, channel, message_data = listen_for_user(slack_client.rtm_read())
            if text and channel:
                # handle_command(command, channel)
                handle_target_user_text(text, channel, message_data)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or Bot ID?")

