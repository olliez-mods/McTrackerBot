import sqlite3

# Returns is a given table exists
def table_exists(cursor: sqlite3.Cursor, name: str) -> bool:
    # Query sqlite_master for metadata on existing tables
    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?", (name,))

    # if a table with a matching name was found, return true
    if(cursor.fetchone()[0] == 1):
        return True
    return False