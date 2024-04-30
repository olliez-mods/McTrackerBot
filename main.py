import sqlite3
import threading
import time

# Returns is a given table exists
def table_exists(cursor: sqlite3.Cursor, name: str) -> bool:
    # Query sqlite_master for metadata on existing tables
    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?", (name,))

    # if a table with a matching name was found, return true
    if(cursor.fetchone()[0] == 1):
        return True
    return False


# Create SQL connection and curser
SQL_connection = sqlite3.connect("McDiscBot.db")
SQL_cursor = SQL_connection.cursor()


# Make sure the tables exist that we want
if(not table_exists(SQL_cursor, "disc_servers")):
    print("Creating \"disc_servers\" SQL table")
    SQL_cursor.execute('''CREATE TABLE disc_servers (
                       server_id INT PRIMARY KEY,
                       server_name VARCHAR(50),
                       owner_id INT,
                       admin_role_id INT,
                       channel_id INT,
                       mc_server_ip VARCHAR(100),
                       mc_server_port INT
                       );''')
    
if(not table_exists(SQL_cursor, "mc_servers")):
    print("Creating \"mc_servers\" SQL table")
    SQL_cursor.execute('''CREATE TABLE mc_servers (
                       server_ip VARCHAR(100) PRIMARY KEY,
                       server_port INT
                       );''')


SQL_connection.close()