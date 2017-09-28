import os
import requests
from slackclient import SlackClient

slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
dictionary_api_key = os.environ.get('DICTIONARY_API_KEY')

def is_admin(user_id):
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'id' in user and user.get('id') == user_id:
                print("Got target user profile for '" + user['id'] + "': " + str(user))
                return user.get('is_admin')

def get_user_id(user_name):
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == user_name:
                user_id = user.get('id')
                print("Got target user id for '" + user['name'] +"': " + user_id)
                return user_id
    else:
        print("could not find bot user with the name " + user_name)

def get_user_name(user_id):
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        users = api_call.get('members')
        for user in users:
            if 'id' in user and user.get('id') == user_id:
                print("Got target user name for '" + user['id'] + "': " + user.get('name'))
                return user.get('name')

def get_channel_name(channel_id):
    print("channel_id: " + channel_id)
    api_call = slack_client.api_call("channels.info", channel=channel_id)
    print(api_call)
    if api_call.get('ok'):
        channel = api_call.get('channel')
        print(channel)
        if 'id' in channel and channel.get('id') == channel_id:
            print("Got target channel name for '" + channel['id'] + "': " + channel.get('name'))
            return channel.get('name')

def get_group_name(group_id):
    print("group_id: " + group_id)
    api_call = slack_client.api_call("groups.info", channel=group_id)
    print(api_call)
    if api_call.get('ok'):
        group = api_call.get('group')
        print(group)
        if 'id' in group and group.get('id') == group_id:
            print("Got target group name for '" + group['id'] + "': " + group.get('name'))
            return group.get('name')

def get_name_from_id(id):
    print("get_name_from_id: " + id)
    if id.startswith("U"):
        return get_user_name(id)
    elif id.startswith("C"):
        return get_channel_name(id)
    elif id.startswith("G"):
        return get_group_name(id)
    elif id.startswith("D"):
        return "direct message"
    else:
        print("get_name_from_id encountered unhandled ID")
        return "unknown"

def send_reply(text, channel):
    slack_client.api_call("chat.postMessage", channel=channel,
                          text=text, as_user=True)

def call_dictionary(word):
    url = ('http://www.dictionaryapi.com/api/v1/references/collegiate/xml/%s?key=%s' %(word, dictionary_api_key))
    print(url)
    response = requests.get(url)
    if response.ok:
        return response
    else:
        print("Encountered error while trying to call dictionary API")

