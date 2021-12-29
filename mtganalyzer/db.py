import datetime
import sqlite3
import os

from mtgaobjects import MtgaDeck, MtgaMatch


DB_FILE="mtganalyzer.db"

######################################################################
## Creates the DB if not exists
#
def initDB():
    if os.path.exists(DB_FILE):
        print("INFO: DB file exists, will use as is.")
        return
    
    conn = sqlite3.connect(DB_FILE)
    try:
        #Create tables
        fin = open("db_init.sql", "rt")
        sql = fin.read()
        conn.executescript(sql)

        print("INFO: DB created successfully")
    finally:
        conn.close()


######################################################################
## Delete the DB file (reserve for dev purpose)
#
def deleteDB():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)



######################################################################
## Stores a match in DB
#
def storeMatch(m : MtgaMatch):
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute('''
        INSERT INTO MATCH (MATCH_ID, OPPONENT_NAME, RESULT, MATCH_START, MATCH_END) 
        SELECT ?, ?, ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM MATCH M2 WHERE M2.MATCH_ID = ?) ;
        ''', [m.matchId, m.opponentName, m.matchOutcomeForYou, m.matchStart, m.matchEnd, m.matchId])

        conn.commit()
    finally:
        conn.close()


######################################################################
## Returns if a file was already processed
#
def fileAlreadyProcessed (path):
    conn = sqlite3.connect(DB_FILE)
    try:
        cur  = conn.cursor()
        cur.execute("SELECT * FROM PROCESSING_HISTORY WHERE FILE_NAME = ? ORDER BY ROWID ASC LIMIT 1", [os.path.basename(path)])

        return len(cur.fetchall()) != 0
    finally:
        conn.close()   
    return False


######################################################################
## Records the file processing in the DB
#
def markFileAsProcessed (path):
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute('''
        INSERT INTO PROCESSING_HISTORY (FILE_NAME, PROCESS_DT) 
        VALUES (?, ?);
        ''', [os.path.basename(path), datetime.datetime.now()])

        conn.commit()
    finally:
        conn.close()    