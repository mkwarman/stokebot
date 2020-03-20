import re
# import json

TAG_CHECK_REGEX = re.compile(r'(<(?:@|#)[^ ]+>)')


def post_message(client, channel_id, text, thread_ts=None,
                 blocks=None):
    client.chat_postMessage(
        channel=channel_id,
        text=text,
        thread_ts=thread_ts,
        blocks=blocks
    )


def post_reply(payload, text, reply_in_thread=None, blocks=None):
    data = payload['data']
    web_client = payload['web_client']
    channel_id = data['channel']
    thread_ts = data['ts'] if 'ts' in data else None

    # Reply in thread if instructed to do so or if no instruction was given
    #   and the payload came from a threaded message
    if (reply_in_thread is True or
       (reply_in_thread is None and 'thread_ts' in data)):
        post_message(web_client, channel_id, text, thread_ts,
                     blocks=blocks)
    else:
        post_message(web_client, channel_id, text, blocks=blocks)


def dm_reply(payload, text, reply_in_thread=None):
    data = payload['data']
    web_client = payload['web_client']
    user = data['user']
    thread_ts = data['ts'] if 'ts' in data else None

    channel_id = get_conversation_id(web_client, user)

    # Reply in thread if instructed to do so or if no instruction was given
    #   and the payload came from a threaded message
    if (reply_in_thread is True or
       (reply_in_thread is None and 'thread_ts' in data)):
        post_message(web_client, channel_id, text, thread_ts)
    else:
        post_message(web_client, channel_id, text)


def react_reply(emoji_name, payload):
    data = payload['data']
    client = payload['web_client']
    channel_id = data['channel']
    timestamp = data['ts']

    client.reactions_add(
        name=emoji_name,
        channel=channel_id,
        timestamp=timestamp
    )


def get_text(payload):
    if 'data' in payload and 'text' in payload['data']:
        return payload['data']['text']
    return None


def get_user_from_payload(payload):
    if ('user' in payload['data']):
        return payload['data']['user']

    return None


def get_real_name_from_id(user_id, client):
    user_info = client.users_info(user=user_id)

    if user_info.get('ok'):
        user = user_info.get('user')
        if 'id' in user and user.get('id') == user_id and 'real_name' in user:
            return user.get('real_name')

    return None


def get_display_name_from_id(user_id, client):
    user_info = client.users_info(user=user_id)

    if user_info.get('ok'):
        user = user_info.get('user')
        if 'id' in user and user.get('id') == user_id and 'profile' in user \
                and 'display_name' in user.get('profile'):
            return user.get('profile').get('display_name')
        elif 'id' in user and user.get('id') == user_id \
                and 'real_name' in user:
            return user.get('real_name')

    return None


def get_first_name_from_id(user_id, client):
    user_info = client.users_info(user=user_id)

    if user_info.get('ok'):
        user = user_info.get('user')
        if 'id' in user and user.get('id') == user_id \
                and 'profile' in user and 'first_name' in user.get('profile'):
            return user.get('profile').get('first_name')
        elif 'id' in user and user.get('id') == user_id \
                and 'real_name' in user:
            return user.get('real_name')

    return None


def get_conversation_id(client, user):
    conversation_info = client.conversations_open(users=user)

    if conversation_info.get('ok'):
        conversation = conversation_info.get('channel')
        if 'id' in conversation:
            return conversation.get('id')

    return None


def to_real_name_if_tag(text, client):
    search_result = TAG_CHECK_REGEX.search(text)

    if search_result:
        tag = search_result.group(1)
        user_id = tag[2:-1].upper()
        return get_real_name_from_id(user_id, client)

    return text


def to_first_name_if_tag(text, client):
    search_result = TAG_CHECK_REGEX.search(text)

    if search_result:
        tag = search_result.group(1)
        user_id = tag[2:-1].upper()
        return get_first_name_from_id(user_id, client)

    return text
