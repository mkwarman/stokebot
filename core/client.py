import re
# import json

TAG_CHECK_REGEX = re.compile(r'(<(?:@|#)[^ ]+>)')


class Client:
    client = None
    silent = False

    def __init__(self, client, silent=False):
        self.client = client
        self.silent = silent

    def post_message(self, channel_id, text=None, thread_ts=None,
                     blocks=None, override_silent=False):
        if (not self.silent) or override_silent:
            self.client.chat_postMessage(
                channel=channel_id,
                text=text,
                thread_ts=thread_ts,
                blocks=blocks
            )
        else:
            data = {'channel': channel_id, 'text': text,
                    'thread_ts': thread_ts, 'blocks': blocks}
            print("posting disabled, would have sent:\n    ", data)

    def post_reply(self, data, text=None, reply_in_thread=None, blocks=None,
                   override_silent=False):
        channel_id = data['channel']
        thread_ts = data['ts'] if 'ts' in data else None

        # Reply in thread if instructed to do so or if no instruction was given
        #   and the message came from a threaded message
        if (reply_in_thread is True or
           (reply_in_thread is None and 'thread_ts' in data)):
            self.post_message(channel_id, text=text, thread_ts=thread_ts,
                              blocks=blocks, override_silent=override_silent)
        else:
            self.post_message(channel_id, text=text, blocks=blocks,
                              override_silent=override_silent)

    def dm_reply(self, data, text, reply_in_thread=None):
        user = data['user']
        thread_ts = data['ts'] if 'ts' in data else None

        channel_id = self.get_conversation_id(user)

        # Reply in thread if instructed to do so or if no instruction was given
        #   and the message came from a threaded message
        if (reply_in_thread is True or
           (reply_in_thread is None and 'thread_ts' in data)):
            self.post_message(channel_id, text, thread_ts)
        else:
            self.post_message(channel_id, text)

    def react_reply(self, data, emoji_name):
        channel_id = data['channel']
        timestamp = data['ts']

        if not self.silent:
            self.client.reactions_add(
                name=emoji_name,
                channel=channel_id,
                timestamp=timestamp
            )
        else:
            data = {'channel': channel_id, 'name': emoji_name,
                    'timestamp': timestamp}
            print("posting disabled, would have reacted:\n    ", data)

    def get_real_name_from_id(self, user_id):
        user_info = self.client.users_info(user=user_id)

        if user_info.get('ok'):
            user = user_info.get('user')
            if 'id' in user and user.get('id') == user_id \
                    and 'real_name' in user:
                return user.get('real_name')

        return None

    def get_display_name_from_id(self, user_id):
        user_info = self.client.users_info(user=user_id)

        if user_info.get('ok'):
            user = user_info.get('user')
            if 'id' in user and user.get('id') == user_id \
                    and 'profile' in user \
                    and 'display_name' in user.get('profile'):
                return user.get('profile').get('display_name')
            elif 'id' in user and user.get('id') == user_id \
                    and 'real_name' in user:
                return user.get('real_name')

        return None

    def get_first_name_from_id(self, user_id):
        user_info = self.client.users_info(user=user_id)

        if user_info.get('ok'):
            user = user_info.get('user')
            if 'id' in user and user.get('id') == user_id \
                    and 'profile' in user \
                    and 'first_name' in user.get('profile'):
                return user.get('profile').get('first_name')
            elif 'id' in user and user.get('id') == user_id \
                    and 'real_name' in user:
                return user.get('real_name')

        return None

    def get_conversation_id(self, user):
        conversation_info = self.client.conversations_open(users=user)

        if conversation_info.get('ok'):
            conversation = conversation_info.get('channel')
            if 'id' in conversation:
                return conversation.get('id')

        return None

    def set_silent(self, silent):
        self.silent = silent

    def to_real_name_if_tag(self, text):
        search_result = TAG_CHECK_REGEX.search(text)

        if search_result:
            tag = search_result.group(1)
            user_id = tag[2:-1].upper()
            return self.get_real_name_from_id(user_id)

        return text

    def to_first_name_if_tag(self, text):
        search_result = TAG_CHECK_REGEX.search(text)

        if search_result:
            tag = search_result.group(1)
            user_id = tag[2:-1].upper()
            return self.get_first_name_from_id(user_id)

        return text
