import datetime

class Definition:
    
    def __init__(self):
        pass
    
    def new(self, word, meaning, user, channel):
        self.word = word
        self.meaning = meaning
        self.user = user
        self.channel = channel
        self.date_time_added = datetime.datetime.now()

    def from_database(self, word, meaning, user, channel, date_time_added):
        self.word = word
        self.meaning = meaning
        self.user = user
        self.channel = channel
        self.date_time_added = date_time_added

    def __repr__(self):
        return ("Test")

    def __str__(self):
        return ("{word: \"" + self.word + "\", " \
                "meaning: \"" + self.meaning + "\", " \
                "user: \"" + self.user + "\", " \
                "channel: \"" + self.channel + "\", " \
                "date_time_added: \"" + str(self.date_time_added) + "\"}")
