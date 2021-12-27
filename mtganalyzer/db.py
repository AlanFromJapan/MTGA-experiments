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
        INSERT INTO MATCH (MATCH_ID, OPPONENT_NAME, RESULT) 
        SELECT ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM MATCH M2 WHERE M2.MATCH_ID = ?) ;
        ''', [m.matchId, m.opponentName, m.matchOutcomeForYou, m.matchId])

        conn.commit()
    finally:
        conn.close()