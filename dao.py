# pylint: disable=C0301
""" Database related functions """
import os
import sqlite3
from sqlite3 import Error

import definition_model
import blacklisted_model
import item_model
from quote_model import Quote

DB_FILE = os.environ.get('DATABASE_FILE')

def create_connection():
    """ create a connection to the SQLite database
    :param DB_FILE: database file
    :return: Connection object or none
    """

    try:
        print(DB_FILE)
        connection = sqlite3.connect(DB_FILE, detect_types=sqlite3.PARSE_DECLTYPES)
        return connection
    except Error as error:
        print("sqlite3 error:" + error)

    return None

# START DEFINITIONS --- START DEFINITIONS --- START DEFINITIONS --- START DEFINITIONS --- START DEFINITIONS --- START DEFINITIONS #

def get_by_id(unique_id):
    """ return word associated with input unique_id """
    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT id, word, relation, meaning, user, channel, date_time_added FROM definitions WHERE id=? '''

    data = (unique_id,)
    cursor.execute(sql, data)

    row = cursor.fetchone()

    if row:
        definition = definition_model.Definition()
        print(row)
        print(str(row[0]) + row[1] + row[2] + row[3] + row[4] + row[5] + str(row[6]))
        definition.from_database(row[0], row[1], row[2], row[3], row[4], row[5], row[6])

        return definition
    #else:
    return None

def delete_by_id(unique_id):
    """ delete definition row based on input unique id """
    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' DELETE FROM definitions WHERE id=? '''

    data = (unique_id,)
    cursor.execute(sql, data)

    print(cursor)
    connection.commit()

    cursor.close()
    connection.close()

def select_all():
    """ return all words defined in the database """

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, word, relation, meaning, user, channel, date_time_added FROM definitions")

    rows = cursor.fetchall()

    definitions = []

    for row in rows:
        definition = definition_model.Definition()
        print(row)
        print(str(row[0]) + row[1] + row[2] + row[3] + row[4] + row[5] + str(row[6]))
        definition.from_database(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        definitions.append(definition)

    cursor.close()
    connection.close()

    return definitions

def insert_definition(definition):
    """ insert definition in the database """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' INSERT INTO definitions(word, relation, meaning, user, channel, date_time_added) values(?, ?, ?, ?, ?, ?) '''

    data = (definition.word, definition.relation, definition.meaning, definition.user, definition.channel, definition.date_time_added)
    print(data)
    cursor.execute(sql, data)
    print(cursor)
    connection.commit()

    cursor.close()
    connection.close()

def read_definition(word):
    """ read all definitions present for a word """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT id, word, relation, meaning, user, channel, date_time_added FROM definitions WHERE word=? '''

    print("word: " + word)
    data = (word,)
    cursor.execute(sql, data)
    print(cursor)

    rows = cursor.fetchall()

    definitions = []

    for row in rows:
        definition = definition_model.Definition()
        print(row)
        print(str(row[0]) + row[1] + row[2] + row[3] + row[4] + row[5] + str(row[6]))
        definition.from_database(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        definitions.append(definition)

    cursor.close()
    connection.close()

    return definitions

def get_defined_words():
    """ read all currently defined words in the database """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT word FROM definitions '''

    cursor.execute(sql)

    rows = cursor.fetchall()

    definitions = [row[0] for row in rows]

    cursor.close()
    connection.close()

    return definitions

# END DEFINITIONS --- END DEFINITIONS --- END DEFINITIONS --- END DEFINITIONS --- END DEFINITIONS --- END DEFINITIONS #

# START BLACKLIST --- START BLACKLIST --- START BLACKLIST --- START BLACKLIST --- START BLACKLIST --- START BLACKLIST #

def get_blacklisted_words():
    """ read all currently blacklisted words in the database """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT word FROM blacklist '''

    cursor.execute(sql)

    rows = cursor.fetchall()

    blacklisted_words = [row[0] for row in rows]

    cursor.close()
    connection.close()

    return blacklisted_words

def get_blacklisted_by_word(word):
    """ return blacklisted word data based on input word """
    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT id, word, user, channel, date_time_added FROM blacklist WHERE word=? '''

    data = (word,)
    cursor.execute(sql, data)

    row = cursor.fetchone()

    if row:
        blacklisted = blacklisted_model.Blacklisted()
        blacklisted.from_database(row[0], row[1], row[2], row[3], row[4])
        return blacklisted
    #else:
    return None

def get_blacklisted_by_id(unique_id):
    """ return blacklisted word data based on input unique id """
    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT id, word, user, channel, date_time_added FROM blacklist WHERE id=? '''

    data = (unique_id,)
    cursor.execute(sql, data)

    row = cursor.fetchone()

    if row:
        blacklisted = blacklisted_model.Blacklisted()
        blacklisted.from_database(row[0], row[1], row[2], row[3], row[4])
        return blacklisted
    #else:
    return None

def insert_blacklisted(blacklisted):
    """ insert blacklisted word in blacklist """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' INSERT INTO blacklist(word, user, channel, date_time_added) values(?, ?, ?, ?) '''

    data = (blacklisted.word, blacklisted.user, blacklisted.channel, blacklisted.date_time_added)
    print(data)
    cursor.execute(sql, data)
    print(cursor)
    connection.commit()

    cursor.close()
    connection.close()

def delete_blacklisted_by_id(unique_id):
    """ delete blacklisted row based on input unique id """
    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' DELETE FROM blacklist WHERE id=? '''

    data = (unique_id,)
    cursor.execute(sql, data)

    print(cursor)
    connection.commit()

    cursor.close()
    connection.close()

def select_all_blacklisted():
    """ return all blacklisted words """

    connection = create_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, word, user, channel, date_time_added FROM blacklist")

    rows = cursor.fetchall()

    blacklist = []

    for row in rows:
        blacklisted = blacklisted_model.Blacklisted()
        blacklisted.from_database(row[0], row[1], row[2], row[3], row[4])

        blacklist.append(blacklisted)

    cursor.close()
    connection.close()

    return blacklist

# END BLACKLIST --- END BLACKLIST --- END BLACKLIST --- END BLACKLIST --- END BLACKLIST --- END BLACKLIST --- END BLACKLIST --- END BLACKLIST #

# START IGNORED USER --- START IGNORED USER --- START IGNORED USER --- START IGNORED USER --- START IGNORED USER --- START IGNORED USER #

def insert_ignored_user(user):
    """ insert ignored user into ignore table """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' INSERT INTO ignore(user_id, user_name, channel, date_time_added) values(?, ?, ?, ?) '''

    data = (user.user_id, user.user_name, user.channel, user.date_time_added)
    print(user)
    cursor.execute(sql, data)
    connection.commit()

    cursor.close()
    connection.close()

def get_ignored_user_ids():
    """ return a list of all ignored user ids """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT user_id FROM ignore '''

    cursor.execute(sql)

    rows = cursor.fetchall()

    ignored = [row[0] for row in rows]

    cursor.close()
    connection.close()

    return ignored

def delete_ignored_by_user_id(user_id):
    """ delete ignored user by user_id """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' DELETE FROM ignore WHERE user_id=? '''

    data = (user_id, )
    cursor.execute(sql, data)
    connection.commit()

    cursor.close()
    connection.close()

# END IGNORED USER --- END IGNORED USER --- END IGNORED USER --- END IGNORED USER --- END IGNORED USER --- END IGNORED USER #

# BEGIN WORD USAGE --- BEGIN WORD USAGE --- BEGIN WORD USAGE --- BEGIN WORD USAGE --- BEGIN WORD USAGE --- BEGIN WORD USAGE #

def increment_word_usage_count(word, times_used):
    """ update times used in word_usage """

    connection = create_connection()
    cursor = connection.cursor()
    sql_insert = ''' INSERT OR IGNORE INTO word_usage(word, times_used) VALUES(?, 0) '''
    sql_update = ''' UPDATE word_usage SET times_used=times_used+? WHERE word LIKE ?; '''

    data_insert = (word, )
    data_update = (times_used, word)

    cursor.execute(sql_insert, data_insert)
    cursor.execute(sql_update, data_update)
    connection.commit()

    cursor.close()
    connection.close()

# END WORD USAGE --- END WORD USAGE --- END WORD USAGE --- END WORD USAGE --- END WORD USAGE --- END WORD USAGE --- END WORD USAGE #
# BEGIN KARMA --- BEGIN KARMA --- BEGIN KARMA --- BEGIN KARMA --- BEGIN KARMA --- BEGIN KARMA --- BEGIN KARMA --- BEGIN KARMA #

def update_karma(key, delta):
    """ Add or remove entity karma """

    connection = create_connection()
    cursor = connection.cursor()
    sql_insert = ''' INSERT OR IGNORE INTO karma(key, karma) VALUES(?, 0) '''
    sql_update = ''' UPDATE karma SET karma=karma+? WHERE key LIKE ?; '''

    data_insert = (key, )
    data_update = (delta, key)

    cursor.execute(sql_insert, data_insert)
    cursor.execute(sql_update, data_update)
    connection.commit()

    cursor.close()
    connection.close()

def get_karma(key):
    """ get entity karma """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT karma FROM karma WHERE key=? '''

    data = (key, )
    cursor.execute(sql, data)

    karma = cursor.fetchone()

    cursor.close()
    connection.close()

    if karma:
        return karma[0]
    #else:
    return None

def get_top_karma(limit):
    """ get top karma entities limited by parameter """

    connection = create_connection()
    cursor = connection.cursor()
    #sql = ''' SELECT * FROM karma ORDER BY karma DESC LIMIT ?; '''
    sql = ''' SELECT * FROM karma WHERE karma IN (SELECT karma FROM karma GROUP BY karma ORDER BY karma DESC LIMIT ?) ORDER BY karma DESC; '''

    data = (limit, )
    cursor.execute(sql, data)

    rows = cursor.fetchall()

    return [(row[0], row[1]) for row in rows]

# END KARMA --- END KARMA --- END KARMA --- END KARMA --- END KARMA --- END KARMA --- END KARMA --- END KARMA --- END KARMA #

# START ITEMS --- START ITEMS --- START ITEMS --- START ITEMS --- START ITEMS --- START ITEMS --- START ITEMS --- START ITEMS #

def insert_item(item):
    """ insert new item """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' INSERT INTO items(name, user_name, channel, date_time_added) values(?, ?, ?, ?) '''

    data = (item.name, item.user_name, item.channel, item.date_time_added)
    print(item)
    cursor.execute(sql, data)
    connection.commit()

    cursor.close()
    connection.close()

def get_items():
    """ return a list of all items currently held """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT name FROM items '''

    cursor.execute(sql)

    rows = cursor.fetchall()

    ignored = [row[0] for row in rows]

    cursor.close()
    connection.close()

    return ignored

def delete_item_by_name(item_name):
    """ delete ignored user by user_id """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' DELETE FROM items WHERE name=? '''

    data = (item_name, )
    cursor.execute(sql, data)
    connection.commit()

    cursor.close()
    connection.close()

def swap_items(new_item_model):
    """ take a new item, swap it with the oldest existing item, and return the old item """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT id, name, user_name, channel, date_time_added FROM items ORDER BY date_time_added ASC LIMIT 1 '''

    # Get oldest item
    cursor.execute(sql)
    row = cursor.fetchone()
    old_item = item_model.Item()
    old_item.from_database(row[0], row[1], row[2], row[3], row[4])

    # Close these. Remaining operations will create their own connections
    cursor.close()
    connection.close()

    # Delete item
    delete_item_by_name(old_item.name)

    # Insert new item
    insert_item(new_item_model)

    return old_item

# START QUOTES --- START QUOTES --- START QUOTES --- START QUOTES --- START QUOTES --- START QUOTES --- START QUOTES #

def insert_quote(quote):
    """ insert new quote """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' INSERT INTO quotes(quote, author, channel, date_time_added) values(?, ?, ?, ?) '''

    data = (quote.quote, quote.author, quote.channel, quote.date_time_added)
    print(quote)
    cursor.execute(sql, data)
    connection.commit()

    cursor.close()
    connection.close()

def get_quotes(author):
    """ Get all quotes by author """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT * FROM quotes WHERE author=?'''

    data = (author, )
    cursor.execute(sql, data)
    rows = cursor.fetchall()

    quotes = []

    for row in rows:
        quote = Quote()
        quote.from_database(row[0], row[1], row[2], row[3], row[4])

        quotes.append(quote)

    cursor.close()
    connection.close()

    return quotes

def get_random_quote(author=None):
    """ Get random quote (by author if present)"""

    connection = create_connection()
    cursor = connection.cursor()

    if author:
        sql = ''' SELECT * FROM quotes WHERE author=? ORDER BY RANDOM() LIMIT 1 '''
        data = (author, )
        cursor.execute(sql, data)
    else:
        sql = ''' SELECT * FROM quotes ORDER BY RANDOM() LIMIT 1 '''
        cursor.execute(sql)

    row = cursor.fetchone()

    if row:
        quote = Quote()
        quote.from_database(row[0], row[1], row[2], row[3], row[4])
    else:
        return None

    cursor.close()
    connection.close()

    return quote

def delete_quote_by_id(quote_id):
    """ Delete quote by ID """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' DELETE FROM quotes WHERE id=? '''

    data = (quote_id, )
    cursor.execute(sql, data)
    connection.commit()

    cursor.close()
    connection.close()

def quote_exists(quote_id):
    """ Determine if quote exists """

    connection = create_connection()
    cursor = connection.cursor()

    # Returns a 1 if row exists and 0 if not
    sql = ''' SELECT EXISTS(SELECT 1 FROM quotes WHERE id=? LIMIT 1) '''

    data = (quote_id, )
    cursor.execute(sql, data)
    exists = cursor.fetchone()

    cursor.close()
    connection.close()

    return exists == 1
