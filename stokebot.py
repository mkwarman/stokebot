import os
import sys
import pkgutil
import slack
from dotenv import load_dotenv

load_dotenv()

# Append core modules directory
sys.path.append('core')

# # Append feature modules directory
# sys.path.append('features')

@slack.RTMClient.run_on(event='message')
def say_hello(**payload):
    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']
    print("data" + str(data))
    trigger_text = ("Hello %s" % (os.getenv("BOT_NAME")))
    if 'text' in data and trigger_text in data['text']:
        channel_id = os.getenv("TEST_CHANNEL_ID")
        thread_ts = data['ts']
        text = "Hi, <@%s>!" % (data['user'])
        
        web_client.chat_postMessage(
            channel=channel_id,
            text=text,
            thread_ts=thread_ts
        )

if __name__ == "__main__":
    client = slack.WebClient(token=os.getenv("SLACK_TOKEN"))

    response = client.chat_postMessage(
            channel='#bottest_private',
            text="Hello world!")
    assert response["ok"]
    assert response["message"]["text"] == "Hello world!"

    rtm_client = slack.RTMClient(token=os.getenv("SLACK_TOKEN"))
    rtm_client.start()
