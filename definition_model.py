import datetime

class Definition:

    def __init__(self):
        pass

    def new(self, word, relation, meaning, user, channel):
        self.word = word
        self.relation = relation
        self.meaning = meaning
        self.user = user
        self.channel = channel
        self.date_time_added = datetime.datetime.now()

    def from_database(self, unique_id, word, relation, meaning, user, channel, date_time_added):
        self.unique_id = unique_id
        self.word = word
        self.relation = relation
        self.meaning = meaning
        self.user = user
        self.channel = channel
        self.date_time_added = date_time_added

    def __str__(self):
        if hasattr(self, 'unique_id'):
            return ("{unique_id: \"" + str(self.unique_id) + "\", " \
                    "word: \"" + self.word + "\", " \
                    "relation: \"" + self.relation + "\", " \
                    "meaning: \"" + self.meaning + "\", " \
                    "user: \"" + self.user + "\", " \
                    "channel: \"" + self.channel + "\", " \
                    "date_time_added: \"" + str(self.date_time_added) + "\"}")

        else:
            return ("{unique_id: [not yet assigned], " \
                    "word: \"" + self.word + "\", " \
                    "relation: \"" + self.relation + "\", " \
                    "meaning: \"" + self.meaning + "\", " \
                    "user: \"" + self.user + "\", " \
                    "channel: \"" + self.channel + "\", " \
                    "date_time_added: \"" + str(self.date_time_added) + "\"}")
