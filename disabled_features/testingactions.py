import os
import threading
from flask import Flask
from core import featurebase


def flask_thread():
    app = Flask(__name__)

    @app.route('/')
    def hello_world():
        return 'Hello world!'

    host = os.getenv("FLASK_HOST")
    port = os.getenv("FLASK_PORT")
    app.run(debug=True, use_reloader=False, host=host, port=port)


class TestingActions(featurebase.FeatureBase):
    thread = None

    def __init__(self):
        thread = threading.Thread(name='Flask app', target=flask_thread)
        thread.setDaemon(True)
        self.thread = thread.start()

# Disabled in favor of Gunicorn
# def get_feature_class():
#     return TestingActions()
