import os
import json
from flask import Flask
from core import builders, helpers, featurebase
from gunicorn.app.base import BaseApplication


def get_config():

    host = os.getenv("LISTEN_HOST")
    port = os.getenv("LISTEN_PORT")

    config = {
        'bind': '%s:%s' % (host, port),
        'workers': 1
    }

    return config


def test_post(client):
    helpers.postMessage(client, os.getenv("PRIVATE_TEST_CHANNEL_ID"),
                        "Test message")
    return "ok"


class StandaloneApplication(BaseApplication):
    # Gunicorn stuff
    def __init__(self, options=None):
        self.options = options or {}
        self.application = self.get_app()
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in self.options.items()
                       if key in self.cfg.settings and value is not None])
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

    # Populate client
    def slack_connected(self, client):
        self.client = client

    # Setup endpoints
    def get_app(self):
        app = Flask(__name__)

        # @app.route('/')
        # def hello_world():
        #     return 'Hello world!'

        # @app.route('/post')
        # def post_message():
        #     return test_post(self.client)

        # @app.route('/command', methods=['POST'])
        # def command_receive():
        #     for key in request.form.keys():
        #         for value in request.form.getlist(key):
        #             print(key, ": ", value)
        #     return "ok"

        # @app.route('/test', methods=['POST'])
        # def test_receive():
        #     for key in request.form.keys():
        #         for value in request.form.getlist(key):
        #             print(key, ": ", value)
        #     return "ok"

        return app


class ActionListener(featurebase.FeatureBase):
    def __init__(self):
        config = get_config()

        self.app = StandaloneApplication(config)

    # def slack_connected(self, client):
    #     self.app.slack_connected(client)

    def ready(self):
        self.app.run()

    def on_command(self, command, payload):
        print("checking for command")
        if (command.lower() == "test interactivity"):
            print("got command")
            bb = builders.BlocksBuilder()
            sb = builders.SectionBuilder()
            ab = builders.ActionsBuilder()
            sb.add_text("This is an interactivity test message")
            bb.add_block(sb.section)
            ab.add_button("Click me?", "this_is_the_button_value")
            bb.add_block(ab.actions)

            helpers.post_reply(payload, blocks=json.dumps(bb.blocks))
            return True


def get_feature_class():
    return ActionListener()
