import datetime

class Quote:

    def __init__(self):
        pass

    def new(self, quote, author, channel):
        self.quote = quote
        self.author = author
        self.channel = channel
        self.date_time_added = datetime.datetime.now()

    def from_database(self, unique_id, quote, author, channel, date_time_added):
        self.unique_id = unique_id
        self.quote = quote
        self.author = author
        self.channel = channel
        self.date_time_added = date_time_added

    def __str__(self):
        if hasattr(self, 'unique_id'):
            return ("{unique_id: \"" + str(self.unique_id) + "\", " \
                    "quote: \"" + self.quote + "\", " \
                    "author: \"" + self.author + "\", " \
                    "channel: \"" + self.channel + "\", " \
                    "date_time_added: \"" + str(self.date_time_added) + "\"}")

        else:
            return ("{unique_id: [not yet assigned], " \
                    "quote: \"" + self.quote + "\", " \
                    "author: \"" + self.author + "\", " \
                    "channel: \"" + self.channel + "\", " \
                    "date_time_added: \"" + str(self.date_time_added) + "\"}")
