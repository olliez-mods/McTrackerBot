import sqlite3

# Returns is a given table exists
def table_exists(cursor: sqlite3.Cursor, name: str) -> bool:
    # Query sqlite_master for metadata on existing tables
    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?", (name,))

    # if a table with a matching name was found, return true
    if(cursor.fetchone()[0] == 1):
        return True
    return False

def create_disc_servers_table(cursor: sqlite3.Cursor):
    cursor.execute('''CREATE TABLE disc_servers (
                   server_id INT PRIMARY KEY,
                   server_name VARCHAR(50),
                   owner_id INT,
                   channel_id INT,
                   pinned_id INT,
                   mc_server_disp_name VARCHAR(50),
                   mc_server_uuid VARCHAR(32),
                   chat_enabled BOOL DEFAULT 0,
                   chat_channel_id INT
                   );''')

def create_mc_servers_table(cursor: sqlite3.Cursor):
    cursor.execute('''CREATE TABLE mc_servers (
                   server_ip VARCHAR(100) PRIMARY KEY,
                   server_port INT,
                   server_uuid VARCHAR(32)
                   );''')

def create_logs_table(cursor: sqlite3.Cursor, uuid: str):
    cursor.execute(f'''CREATE TABLE LOGS_{uuid} (
                   timestamp DATETIME,
                   s_reboot BOOL,
                   connected BOOL,
                   online BOOL,
                   player_count INT,
                   players TEXT
                   );''')
    
def create_chat_servers_table(cursor: sqlite3.Cursor):
    cursor.execute(f'''CREATE TABLE chat_servers (
                   
                   );''')