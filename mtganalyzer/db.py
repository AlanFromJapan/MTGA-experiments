import datetime
import sqlite3
import os
from typing import Dict

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
        fin = open("sql/db_init.sql", "rt")
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
        INSERT INTO MATCH (MATCH_ID, OPPONENT_NAME, RESULT, MATCH_START, MATCH_END, DECK_ID) 
        SELECT ?, ?, ?, ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM MATCH M2 WHERE M2.MATCH_ID = ?) ;
        ''', [m.matchId, m.opponentName, m.matchOutcomeForYou, m.matchStart, m.matchEnd, m.deck.deckId if m.deck != None else None, m.matchId])

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
def markFileAsProcessed (path, goldAndGems = None):
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute('''
        INSERT INTO PROCESSING_HISTORY (FILE_NAME, PROCESS_DT, CLOSING_GEM, CLOSING_GOLD) 
        VALUES (?, ?, ?, ?);
        ''', [os.path.basename(path), datetime.datetime.now(), None if goldAndGems is None else goldAndGems[1], None if goldAndGems is None else goldAndGems[0]])

        conn.commit()
    finally:
        conn.close()    



######################################################################
## Stores a DECK in DB
#
def storeDeck(d : MtgaDeck):
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute('''
        INSERT INTO DECK (DECK_ID, DECK_NAME, MANA, TILE_ARENAID) 
        SELECT ?, ?, ?, ?
        WHERE NOT EXISTS (SELECT 1 FROM DECK D2 WHERE D2.DECK_ID = ?) ;
        ''', [d.deckId, d.name, d.mana, d.tileCardArenaID, d.deckId])

        conn.commit()
    finally:
        conn.close()



######################################################################
## Update a DECK tile's URL in DB
#
def saveDeckURL(d : MtgaDeck):
    conn = sqlite3.connect(DB_FILE)
    try:
        conn.execute('''
        UPDATE DECK SET TILE_URL_SMALL = ? WHERE DECK_ID = ? ;
        ''', [d.tileURL, d.deckId])

        conn.commit()
    finally:
        conn.close()



######################################################################
## Returns last match (match list)
#
def getMatchLatest (count: int = 10):
    conn = sqlite3.connect(DB_FILE)
    try:
        cur  = conn.cursor()
        cur.execute("SELECT * FROM MATCH M JOIN DECK D ON M.deck_Id = D.deck_Id ORDER BY M.MATCH_START DESC LIMIT ?", [count])

        rows = cur.fetchall()

        matches = []
        for row in rows:
            m = MtgaMatch(row[0], row[4], row[1], 0, row[5], row[3])
            d = MtgaDeck(row[8], row[10], row[7], row[9], row[11])
            m.deck = d
            matches.append(m)

        return matches
    finally:
        conn.close()   
    return False




######################################################################
## Returns stats about decks
#
def getDeckStats (deckId = None):
    conn = sqlite3.connect(DB_FILE)
    try:
        params = {"id" : deckId }
        #get the results with column names and not only index https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory
        conn.row_factory = sqlite3.Row
        #in that order
        cur  = conn.cursor()
        cur.execute("""
select d.*, 
(SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id) as TotalMatch,
(SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id AND m.RESULT = "Victory") as TotalWin,
(SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id AND m.RESULT = "Defeat") as TotalLoss,
printf("%d", (SELECT AVG(strftime('%s', m.MATCH_END) - strftime('%s', m.MATCH_START)) FROM MATCH m WHERE m.deck_id = d.deck_id)) as AvgMatchLengthInSec,
COALESCE(CAST(100.00 * (1.00 * (SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id AND m.RESULT = "Victory")) / (1.00 * (SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id)) as int), 0) as WinRatioPercent

from DECK d
WHERE :id IS NULL OR (:id IS NOT NULL AND d.deck_id = :id)   
ORDER BY DECK_NAME ASC ;    
        """, params)

        res = []
        for row in cur.fetchall():
            #print(row["TotalMatch"])
            res.append(dict_from_row(row))
        
        return res
    finally:
        conn.close()  

def dict_from_row(row):
    return dict(zip(row.keys(), row))       



######################################################################
## Returns general stats 
#
def getGeneralStats ():
    return __executeScriptAndReturn("getStats.sql", "SELECT * FROM tmpStats;")


######################################################################
## Returns decks colors stats 
#
def getDecksColorsStats ():
    return __executeScriptAndReturn("getDecksColorsStats.sql", "SELECT * FROM tmpStats;")


######################################################################
## Delete today's data
#
def deleteTodaysData ():
    return __executeScriptAndReturn("deleteTodaysData.sql")


######################################################################
## Executes a script and then a one liner (typically long script + read result)
#
def __executeScriptAndReturn (scriptFileName: str, returnSql : str = None):
    conn = sqlite3.connect(DB_FILE)
    try:
        #get the results with column names and not only index https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory
        conn.row_factory = sqlite3.Row
        #in that order
        cur  = conn.cursor()
        
        scriptFile = os.path.join(".", os.path.join("sql",  scriptFileName))
        #print ("DBG: execute script " + scriptFile)

        content = open(scriptFile, "rt").read()
        #print("DBG content: " + content)

        #executes the script but does not return content of the final "SELECT", have to do it after with an regular execute
        cur.executescript(content)
        conn.commit()
        
        #read the result
        if not returnSql is None:
            cur.execute(returnSql)
            
            #make an array of dict of the output
            res = []
            for row in cur.fetchall():
                #print("DBG row=" + str(row))
                res.append(dict_from_row(row))
            
            return res
        else:
            return None
    except Exception as ex:
        print ("ERROR in __executeScriptAndReturn() : " + str(ex))
        conn.rollback()
        return None
    finally:
        conn.close()  