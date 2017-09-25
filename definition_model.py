

class Definition:
    
    def __init__(self):
        pass
    
    def new(self, word, definition, added_by_user, added_in_channel):
        self.word = word
        self.definition = definition
        self.added_by_user = added_by_user
        self.added_in_channel = added_in_channel

    def from_database(self, word, definition, date_added, time_added, added_by_user, added_in_channel):
        self.word = word
        self.definition = definition
        self.date_added = date_added
        self.time_added = time_added
        self.added_by_user = added_by_user
        self.added_in_channel = added_in_channel
