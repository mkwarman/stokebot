def postMessage(client, channel_id, text):
    client.chat_postMessage(
        channel=channel_id,
        text=text
    )

def postThreadMessage(client, channel_id, thread_ts, text):
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=text
    )

def postReply(payload, text, reply_in_thread):
    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']
    channel_id = data['channel']
    thread_ts = data['ts'] if 'ts' in data else None

    if reply_in_thread:
        postThreadMessage(client, channel_id, thread_ts, text)
    else:
        postMessage(client, channel_id, text)

