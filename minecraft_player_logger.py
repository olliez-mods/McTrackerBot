import sqlite3
import time
from datetime import datetime
from SQL_functions import *
from get_mc_server_status import *
import uuid


def get_uuid() -> str:
    return str(uuid.uuid4())

def start(sql_database: str, timeout: int=10):

    # Keeps track of how long an iteration took so we can calculate how long to time.sleep() for
    iteration_start: float=0.0
    iteration_end: float=0.0

    # Create SQL connection and curser
    SQL_connection = sqlite3.connect(sql_database)
    SQL_cursor = SQL_connection.cursor()

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


            status = get_status(ip, port)

            timestamp = str(datetime.now())

            SQL_cursor.execute(f"INSERT INTO LOGS_{uuid} (timestamp, connection, online, player_count, players) VALUES ('{timestamp}', '{status['connected']}', '{status['online']}', '{status['count']}', '{','.join(status['players'])}')")
            SQL_connection.commit()


        iteration_end = time.time()
        time.sleep(timeout - (iteration_end-iteration_start))
    