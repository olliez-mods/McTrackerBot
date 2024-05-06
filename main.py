import sqlite3
import threading
import time
import configparser
from SQL_functions import *
import minecraft_player_logger as MC_Logger
import discord_bot as Discord_Bot

# Read in config file
config = configparser.ConfigParser()
config.read('config.ini')

# Assign config to static variables
USE_BOT: bool = (config['Settings']['use_bot'] == "1")
BOT_TOKEN: str = config['Settings']['bot_token']
SQL_DATABASE: str = config['Settings']['SQL_database']
STATUS_TIMEOUT: int = int(config['Settings']["status_update_timeout"])
PINNED_TIMEOUT: int = int(config['Settings']["pinned_message_timeout"])

# Create SQL connection and curser
SQL_connection = sqlite3.connect(SQL_DATABASE)
SQL_cursor = SQL_connection.cursor()


# Make sure the disc_servers table exists if we are using the bot
if(USE_BOT and not table_exists(SQL_cursor, "disc_servers")):
    print("Creating \"disc_servers\" SQL table")
    create_disc_servers_table(SQL_cursor)
    
# Make sure the mc_servers table exists
if(not table_exists(SQL_cursor, "mc_servers")):
    print("Creating \"mc_servers\" SQL table")
    create_mc_servers_table(SQL_cursor)

def run_discord_bot():
    Discord_Bot.start(SQL_DATABASE, BOT_TOKEN, PINNED_TIMEOUT)
def run_mc_bot():
    MC_Logger.start(SQL_DATABASE, STATUS_TIMEOUT)

discord_bot_thread = threading.Thread(target=run_discord_bot)
minecraft_bot_thread = threading.Thread(target=run_mc_bot)
discord_bot_thread.daemon = True
minecraft_bot_thread.daemon = True

if(USE_BOT): discord_bot_thread.start()
minecraft_bot_thread.start()

try:
    exit_ = input("")
except KeyboardInterrupt:
    pass

SQL_connection.close()