import re

TAG_CHECK_REGEX = re.compile(r'(<(?:@|#)[^ ]+>)')

def post_message(client, channel_id, text):
    client.chat_postMessage(
        channel=channel_id,
        text=text
    )

def post_thread_message(client, channel_id, thread_ts, text):
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=text
    )

def post_reply(payload, text, reply_in_thread = False):
    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']
    channel_id = data['channel']
    thread_ts = data['ts'] if 'ts' in data else None

    if reply_in_thread:
        post_thread_message(web_client, channel_id, thread_ts, text)
    else:
        post_message(web_client, channel_id, text)

def get_text(payload):
    if 'data' in payload and 'text' in payload['data']:
        return payload['data']['text']
    return None

def to_first_name_if_tag(text, client):
    search_result = TAG_CHECK_REGEX.search(text)

    if search_result:
        tag = search_result.group(1)
        user_id = tag[2:-1].upper()
        user_info = client.users_info(user = user_id)

        if not user_info.get('ok'):
            return text

        user = user_info.get('user')
        if 'id' in user and user.get('id') == user_id and 'profile' in user and 'first_name' in user.get('profile'):
            return user.get('profile').get('first_name')
        elif 'id' in user and user.get('id') == user_id and 'real_name' in user:
            return user.get('real_name')

    return text

