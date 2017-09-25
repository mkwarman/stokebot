import sqlite3
from sqlite3 import Error


def create_connection(df_file):
    """ create a connection to the SQLite database
    :param db_file: database file
    :return: Connection object or none
    """

    try:
        connection = sqlite3.connect(db_file)
        return connection
    except Error as e:
        print(e)

    return None


def select_all_words(connection):
    """ return all words defined in the database """

    cursor = connection.cursor()
    cursor.execute("SELECT * FROM definitions")

    rows = cursor.fetchall()

    return rows


#def insert_definition(definition):

