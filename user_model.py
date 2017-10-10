import datetime

class User:

    def __init__(self):
        pass

    def new(self, user_id, user_name, channel):
        self.user_id = user_id
        self.user_name = user_name
        self.channel = channel
        self.date_time_added = datetime.datetime.now()

    def from_database(self, unique_id, user_id, user_name, channel, date_time_added):
        self.unique_id = unique_id
        self.user_id = user_id
        self.user_name = user_name
        self.channel = channel
        self.self.date_time_added = date_time_added

    def __str__(self):
        if hasattr(self, 'unique_id'):
            return ("{unique_id: \"" + str(self.unique_id) + "\", " \
                    "user_id: \"" + self.user_id + "\", " \
                    "user_name: \"" + self.user_name + "\", "\
                    "channel: \"" + self.channel + "\", "\
                    "date_time_added: \"" + str(self.date_time_added) + "\"}")
        else:
            return ("{unique_id: [not yet assigned], " \
                    "user_id: \"" + self.user_id + "\", " \
                    "user_name: \"" + self.user_name + "\", "\
                    "channel: \"" + self.channel + "\", "\
                    "date_time_added: \"" + str(self.date_time_added) + "\"}")
