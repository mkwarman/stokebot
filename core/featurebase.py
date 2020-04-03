class FeatureBase:
    def slack_connected(self, client):
        pass

    def on_message(self, text, data):
        pass

    # If a feature recognizes a command, it should return True.
    # If no features return True, the user will recieve a "command not
    #   recognized message
    def on_command(self, command, data):
        pass

    def on_me_message(self, text, data):
        pass

    # Features should use the BlocksBuilder class to create blocks that
    #   contain help information
    def get_help(self):
        pass
