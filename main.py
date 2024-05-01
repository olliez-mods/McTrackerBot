import sqlite3
import threading
import time
import configparser
from SQL_functions import *
from global_flags import *
import minecraft_player_logger as MC_Logger

# Read in config file
config = configparser.ConfigParser()
config.read('config.ini')

# Assign config to static variables
USE_BOT: bool = (config['Settings']['use_bot'] == "1")
BOT_TOKEN: str = config['Settings']['bot_token']
SQL_DATABASE: str = config['Settings']['SQL_database']
STATUS_TIMEOUT: int = int(config['Settings']["status_update_timeout"])

# Create SQL connection and curser
SQL_connection = sqlite3.connect(SQL_DATABASE)
SQL_cursor = SQL_connection.cursor()


# Make sure the disc_servers table exists if we are using the bot
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
    
# Make sure the mc_servers table exists
if(not table_exists(SQL_cursor, "mc_servers")):
    print("Creating \"mc_servers\" SQL table")
    SQL_cursor.execute('''CREATE TABLE mc_servers (
                       server_ip VARCHAR(100) PRIMARY KEY,
                       server_port INT,
                       server_uuid VARCHAR(32)
                       );''')


def run_discord_bot():
    pass
def run_mc_bot():
    MC_Logger.start(SQL_DATABASE, STATUS_TIMEOUT)

discord_bot_thread = threading.Thread(target=run_discord_bot)

minecraft_bot_thread = threading.Thread(target=run_mc_bot)
kill_mc_bot = False

if(USE_BOT): discord_bot_thread.start()
minecraft_bot_thread.start()

exit_ = input("enter to exit at any point")

SQL_connection.close()