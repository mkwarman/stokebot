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

if __name__ == "__main__":
    client = slack.WebClient(token=os.getenv("SLACK_TOKEN"))

    response = client.chat_postMessage(
            channel='#bottest_private',
            text="Hello world!")
    assert response["ok"]
    assert response["message"]["text"] == "Hello world!"
