class FeatureBase:
    def slack_connected(self, client):
        pass

    def ready(self):
        pass

    def on_message(self, text, payload):
        pass

    # If a feature recognizes a command, it should return True. If not, the user will recieve a "command not recognized" message
    def on_command(self, command, payload):
        pass
