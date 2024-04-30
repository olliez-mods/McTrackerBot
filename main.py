import sqlite3
import threading
import time
import configparser
from SQL_functions import *

# Read in config file
config = configparser.ConfigParser()
config.read('config.ini')

# Assign config to static variables
USE_BOT: bool = (config['Settings']['use_bot'] == "1")
BOT_TOKEN: str = config['Settings']['bot_token']
SQL_DATABASE: str = config['Settings']['SQL_database']

# Create SQL connection and curser
SQL_connection = sqlite3.connect(SQL_DATABASE)
SQL_cursor = SQL_connection.cursor()


# Make sure the tables exist that we want
if(USE_BOT and not table_exists(SQL_cursor, "disc_servers")):
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


def run_discord_bot():
    pass

def run_mc_bot():
    pass



SQL_connection.close()