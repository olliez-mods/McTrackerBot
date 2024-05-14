import sqlite3
import threading
import time
import requests
import os
import configparser
from SQL_functions import *
import minecraft_player_logger as MC_Logger
import discord_bot as Discord_Bot

import socket

# If the config.ini file doesn't exist yet, we will make a default version of it and then quit
if(not os.path.exists('config.ini')):
    print("Default config.ini file created with default settings.\nPlease adjust these for the program to function correctly")
    with open('config.ini', 'w') as f:
        f.write("""
# Config file to setup the discord bot
# use 1 for True (or yes), 0 for False (or no)

[Settings]
# Should the bot be activated? If so you need to provide a bot_token
use_bot=1
bot_token=
owner_id=475093793834663948

# Name of the .db file you will be using (can be anything)
SQL_database=bot_database.db

# Timeout between pinging every minecraft server
status_update_timeout=3
# Timeout between updating pinned messages (May be rate limited if beloew 10)
pinned_message_timeout=10
                
# Wait for internet connection before attempting to start. (If set to 0, we will quit immediately)
wait_for_connection_on_boot=0
# How many seconds to wait before just giving up and quitting (set to -1 no never quit!)
time_before_fail=180
""")
    exit()

# Read in config file
config = configparser.ConfigParser()
config.read('config.ini')

# Assign config to static variables
USE_BOT: bool = (config['Settings']['use_bot'] == "1")
BOT_TOKEN: str = config['Settings']['bot_token']
OWNER_ID: int = int(config['Settings']['owner_id'])
SQL_DATABASE: str = config['Settings']['SQL_database']
STATUS_TIMEOUT: int = int(config['Settings']["status_update_timeout"])
PINNED_TIMEOUT: int = int(config['Settings']["pinned_message_timeout"])
WAIT_FOR_CONNECTION: bool = (config['Settings']['wait_for_connection_on_boot'] == "1")
TIME_BEFORE_FAIL:int = int(config['Settings']['time_before_fail'])

# Function that return True if we have internet access
def check_internet_connection():
    try:
        response = requests.get("http://www.google.com", timeout=5)
        return response.status_code == 200
    except requests.ConnectionError:
        return False
if(not check_internet_connection()):
    # If we don't have internet but user wants us to quit. sigh, do it.
    if(not WAIT_FOR_CONNECTION):
        print("Internet connection not found :(. Goodbye\n")
        exit()
    print(f"Internet connection not found (Timeout={TIME_BEFORE_FAIL}):")
    print(" - Waiting...  ", end="", flush=True)
    t_start = time.time()
    # As long as we don't have internet keep going around and around
    while(not check_internet_connection()):
        # If it's -1 we want to loop inf. Otherwise check if we've hit our timeout
        if(TIME_BEFORE_FAIL > -1 and time.time() - t_start > TIME_BEFORE_FAIL):
            print("\n - Couldn't connect to the internet in time :(. Goodbye\n")
            exit()
        time.sleep(1)
        # Using \r here return us to the beggining of the line, so we print over what we just printed
        print(f"\r - Waiting... {int(time.time() - t_start)}", flush=True, end="")
    print("\n - Internet connection established :D\n")


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
    if(BOT_TOKEN == "" or BOT_TOKEN == " " or len(BOT_TOKEN) < 20 or not ('.' in BOT_TOKEN)):
        print("The provided token seems to not be formatted correctly. Make sure you are using the correct token\n")
        exit()
    Discord_Bot.start(SQL_DATABASE, BOT_TOKEN, OWNER_ID, PINNED_TIMEOUT)

def run_mc_bot():
    MC_Logger.start(SQL_DATABASE, STATUS_TIMEOUT)

discord_bot_thread = threading.Thread(target=run_discord_bot)
minecraft_bot_thread = threading.Thread(target=run_mc_bot)
discord_bot_thread.daemon = True
minecraft_bot_thread.daemon = True

if(USE_BOT): discord_bot_thread.start()
minecraft_bot_thread.start()

while(discord_bot_thread.is_alive() and minecraft_bot_thread.is_alive()):
    time.sleep(2)