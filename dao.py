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
    sql = ''' SELECT * FROM blacklist WHERE word=? '''

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
    sql = ''' SELECT * FROM blacklist WHERE id=? '''

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
    cursor.execute("SELECT * FROM blacklist")

    rows = cursor.fetchall()

    blacklist = []

    for row in rows:
        blacklisted = blacklisted_model.Blacklisted()
        print(row)
        print(str(row[0]) + row[1] + row[2] + row[3] + str(row[4]))
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


