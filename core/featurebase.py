class FeatureBase:
    def slack_connected(self, client):
        pass

    def ready(self):
        pass

    def on_message(self, text, data, client):
        pass

    # If a feature recognizes a command, it should return True.
    # If no features return True, the user will recieve a "command not
    #   recognized message
    def on_command(self, command, data, client):
        pass

    def on_me_message(self, text, data, client):
        pass

    # Features should use the BlocksBuilder class to create blocks that
    #   contain help information
    def get_help(self):
        pass
