import sqlite3
import time
from datetime import datetime
from SQL_functions import *
from get_mc_server_status import *
import uuid


def get_uuid() -> str:
    return str(uuid.uuid4())

def add_record(connection: sqlite3.Connection, cursor: sqlite3.Cursor, uuid: str, timestamp: str, s_reboot: int, connected: int, online: int, player_count: int, players: list[str]):
    cursor.execute(f"INSERT INTO LOGS_{uuid} (timestamp, s_reboot, connected, online, player_count, players) VALUES ('{timestamp}', {s_reboot}, {connected}, {online}, {player_count}, '{','.join(players)}')")
    connection.commit()

def start(sql_database: str, timeout: int=10):

    # Keeps track of how long an iteration took so we can calculate how long to time.sleep() for
    iteration_start: float=0.0
    iteration_end: float=0.0

    # Create SQL connection and curser
    SQL_connection = sqlite3.connect(sql_database)
    SQL_cursor = SQL_connection.cursor()

    timestamp = str(datetime.now())

    while(True):
        iteration_start = time.time()

        #First get all servers we need to ping (This may be updated between iterations)
        SQL_cursor.execute('SELECT * FROM mc_servers')
        rows: list[any] = SQL_cursor.fetchall()
        

        #Loop through each server
        for mc_server in rows:
            ip: str = mc_server[0]
            port: int = mc_server[1]
            uuid: str = mc_server[2]

            if(not table_exists(SQL_cursor, f"LOGS_{uuid}")):
                print("New unlogged server... creating TABLE")
                create_logs_table(SQL_cursor, uuid)

            # Returns None if the row isn't found
            SQL_cursor.execute(f"SELECT * FROM LOGS_{uuid} ORDER BY timestamp DESC LIMIT 1")

            # Fetch the result (the row with the most recent datetime value)
            last_log = SQL_cursor.fetchone()

            status = get_status(ip, port)
            if('players' in status): status['players'].sort()

            make_log = False
            if(last_log == None): make_log = True
            elif(status['connected'] != last_log[2]): make_log = True
            elif(status['online'] != last_log[3]): make_log = True
            elif(status['count'] != last_log[4]): make_log = True
            elif(len(last_log) >= 6 and not all(x == y for x, y in zip(status['players'], last_log[5].split(",")))): make_log = True

            if(make_log):
                timestamp = str(datetime.now())
                add_record(SQL_connection, SQL_cursor, uuid, timestamp, 0, status['connected'], status['online'], status['count'], status['players'])

        iteration_end = time.time()

        tts = timeout - (iteration_end-iteration_start)
        if(tts < 0): tts = 0
        time.sleep(tts)
    