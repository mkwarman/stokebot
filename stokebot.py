import os
import time
from slackclient import SlackClient

# constants
BOT_NAME = "stokebot"
TARGET_USER_NAME = "mkwarman"
EXAMPLE_COMMAND = "do"

# globals
global at_bot_id
global at_target_user_id

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))


def get_user_id(user_name):
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == user_name:
                print("Got target user id for '" + user['name'] +"': " + user.get('id'))
                return user.get('id')
    else:
        print("could not find bot user with the name " + BOT_NAME)

def example_handle_command(command, channel):
    """
    	Receives commands directed at the bot and determines if they
    	are valid commands. If so, then acts on the commmands. If not,
    	returns back what it needs for clariication.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
    	   "* command with numbers, delimited by spaces."
    if command.startswith(EXAMPLE_COMMAND):
    	response = "Sure... write some more code and I can do that!"
    slack_client.api_call("chat.postMessage", channel=channel,
    	             	  text=response, as_user=True)

def handle_target_user_text(text, channel):
    print("Handling target user text")
    response = "Target user said: " + text
    print("Sending \"chat.postMessage\":" \
            "\n  channel=\"" + channel + "\"" \
            "\n  text=\"" + response + "\"" \
            "\n  as_user=True")
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def example_parse_slack_output(slack_rtm_output):
    """
    	The Slack Real Time Messaging API is the events firehose.
    	this parsing function returns None unless a message is
    	directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
    	for output in output_list:
    	    if output and 'text' in output and at_bot_id in output['text']:
    	    	# return text after the @mention, whitespace removed
    	    	return output['text'].split(at_bot_id)[1].strip().lower(), \
    	    	       output['channel']
    return None, None

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
                return output['text'].strip().lower(), output['channel']
                # return None, None
    return None, None



if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StokeBot connected and running!")
        global at_bot_id
        global at_target_user_id
        at_bot_id = get_user_id(BOT_NAME) # Get the bot's ID
        at_target_user_id = get_user_id(TARGET_USER_NAME) # Get the target user's ID

        while True:
            text, channel = listen_for_user(slack_client.rtm_read())
            if text and channel:
                # handle_command(command, channel)
                handle_target_user_text(text, channel)
                time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or Bot ID?")
