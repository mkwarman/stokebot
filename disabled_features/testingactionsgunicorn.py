import os
from flask import Flask, request
from core import helpers, featurebase
from gunicorn.app.base import BaseApplication
from gunicorn.six import iteritems


def get_config():

    host = os.getenv("LISTEN_HOST")
    port = os.getenv("LISTEN_PORT")

    config = {
        'bind': '%s:%s' % (host, port),
        'workers': 1
    }

    return config


def test_post(client):
    helpers.postMessage(client, os.getenv("TEST_CHANNEL_ID"), "Test message")
    return "ok"


class StandaloneApplication(BaseApplication):
    # Gunicorn stuff
    def __init__(self, options=None):
        self.options = options or {}
        self.application = self.get_app()
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = dict([(key, value) for key, value in iteritems(self.options)
                       if key in self.cfg.settings and value is not None])
        for key, value in iteritems(config):
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application

    # Populate client
    def slack_connected(self, client):
        self.client = client

    # Setup endpoints
    def get_app(self):
        app = Flask(__name__)

        @app.route('/')
        def hello_world():
            return 'Hello world!'

        @app.route('/post')
        def post_message():
            return test_post(self.client)

        @app.route('/test', methods=['POST'])
        def test_receive():
            for key in request.form.keys():
                for value in request.form.getlist(key):
                    print(key, ": ", value)
            return "ok"

        return app


class ActionListener(featurebase.FeatureBase):
    def __init__(self):
        config = get_config()

        self.app = StandaloneApplication(config)

    def slack_connected(self, client):
        self.app.slack_connected(client)

    def ready(self):
        self.app.run()


def get_feature_class():
    return ActionListener()
