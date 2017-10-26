import os
import sqlite3
import definition_model
import blacklisted_model
from slackclient import SlackClient
from sqlite3 import Error


db_file = os.environ.get('DATABASE_FILE')

def create_connection():
    """ create a connection to the SQLite database
    :param db_file: database file
    :return: Connection object or none
    """

    try:
        print(db_file)
        connection = sqlite3.connect(db_file, detect_types=sqlite3.PARSE_DECLTYPES)
        return connection
    except Error as e:
        print(e)

    return None

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
    else:
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
    else:
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

def get_by_id(unique_id):
    """ return word associated with input unique_id """
    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' SELECT * FROM definitions WHERE id=? '''

    data = (unique_id,)
    cursor.execute(sql, data)

    row = cursor.fetchone()

    if row:
        definition = definition_model.Definition()
        print(row)
        print(str(row[0]) + row[1] + row[2] + row[3] + row[4] + str(row[5]))
        definition.from_database(row[0], row[1], row[2], row[3], row[4], row[5])

        return definition
    else:
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
    cursor.execute("SELECT * FROM definitions")

    rows = cursor.fetchall()

    definitions = []

    for row in rows:
        definition = definition_model.Definition()
        print(row)
        print(str(row[0]) + row[1] + row[2] + row[3] + row[4] + str(row[5]))
        definition.from_database(row[0], row[1], row[2], row[3], row[4], row[5])
        definitions.append(definition)

    cursor.close()
    connection.close()

    return definitions

def insert_definition(definition):
    """ insert definition in the database """

    connection = create_connection()
    cursor = connection.cursor()
    sql = ''' INSERT INTO definitions(word, meaning, user, channel, date_time_added) values(?, ?, ?, ?, ?) '''

    data = (definition.word, definition.meaning, definition.user, definition.channel, definition.date_time_added)
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
    sql = ''' SELECT * FROM definitions WHERE word=? '''

    print("word: " + word)
    data = (word,)
    cursor.execute(sql, data)
    print(cursor)

    rows = cursor.fetchall()

    definitions = []

    for row in rows:
        definition = definition_model.Definition()
        print(row)
        print(str(row[0]) + row[1] + row[2] + row[3] + row[4] + str(row[5]))
        definition.from_database(row[0], row[1], row[2], row[3], row[4], row[5])
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
