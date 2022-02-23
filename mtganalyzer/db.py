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
def saveDeckTileURL(d : MtgaDeck):
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
def getMatchLatest (count: int = 10, offset: int = 0):
    conn = sqlite3.connect(DB_FILE)
    try:
        cur  = conn.cursor()
        cur.execute("""
        SELECT * 
        FROM MATCH M JOIN DECK D ON M.deck_Id = D.deck_Id 
        ORDER BY M.MATCH_START DESC 
        LIMIT ?, ?""", [offset, count])

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




######################################################################
## Returns stats about ALL decks
#
def getDeckStats ():
    return __executeScriptAndReturn("getDecksStats.sql", "SELECT * FROM TMPDECKSTATS;")


######################################################################
## Returns win-loss history of ONE deck
#
def getDeckWinlossHistory (deckID : str):
    return __executeScriptAndReturn("getDeckWinLossHistory.sql", "SELECT * FROM tmpStats;", {"DeckID" : deckID})
     



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
def __executeScriptAndReturn (scriptFileName: str, returnSql : str = None, params : dict = {}):
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

        #apply params
        for key in params:
            content = content.replace("@@" + key, params[key])

        #print("DBG UPDATED content: " + content)

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

# Helper method for __executeScriptAndReturn()
def dict_from_row(row):
    return dict(zip(row.keys(), row))  