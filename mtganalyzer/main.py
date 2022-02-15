from datetime import datetime, timedelta
from sqlite3.dbapi2 import paramstyle
from flask import Flask, render_template, redirect, url_for, request, make_response
import os, sys
import logging
from logging.handlers import RotatingFileHandler
import re
import werkzeug 
import operator
import time

import config

from mtgaobjects import MtgaDeck, MtgaMatch
import mtgalib
import mtgalogs
import db


########################################################################################
## Flask vars
#
app = Flask(__name__, static_url_path='')

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ico'])

########################################################################################
## Flask init
#
@app.before_first_request
def init():
    #Init
    myPlayerId = config.myconfig["my_userId"]
    print ("My user id " + myPlayerId)

    #DB setup
    #db.deleteDB()
    db.initDB()

    #scanner init
    scanner = mtgalogs.MtgaLogScanner(myPlayerId)

    #scan 
    paramPath = str(sys.argv[1])
    if ".log" == paramPath[-4:].lower():
        #scan 1 file
        scanOneFile(scanner, paramPath)
    else:
        #assume it's a folder
        for f in os.listdir(paramPath):
            path2file = os.path.join(paramPath, f)
            if os.path.isfile(path2file) and ".log" == path2file[-4:].lower():
                scanOneFile(scanner, path2file)



########################################################################################
## Web related functions
#
@app.route('/')
def homepage():
    stats = db.getGeneralStats()

    return render_template("home01.html", pagename="Home", stats=stats) # dbg=stats)



@app.route('/about')
def aboutPage():
    return render_template("template01.html", pagename="About", pagecontent='''
About MTGAnalyzer<br/>
<br/>
By AlanFromJapan / MIT license / Full source code here <a href="https://github.com/AlanFromJapan/MTGA-experiments">on Github</a>.<br/>
This application is not approved nor affiliated with WotC or Hasbro or anyone.<br/>
Don't sue me, go play MtGA instead.
    ''')



@app.route('/matchhistory', methods=['GET'])
def matchHistoryPage():
    PAGE_LEN = 15
    offset = 0

    if "curPage" in request.args :
        offset = int(request.args["curPage"]) 
    else:
        offset = 0
    if "action" in request.args :
        if request.args["action"] == "prev":
            offset = 0 if offset <= 0 else offset - 1 
        elif request.args["action"] == "next":
            offset = offset + 1
    
    matches = db.getMatchLatest(count=PAGE_LEN, offset=offset * PAGE_LEN)
    stats = dict()
    stats["total"] = 0
    stats["win"] = 0

    for m in matches:
        stats["total"] = stats["total"] +1
        stats["win"] = stats["win"] + (1 if m.matchOutcomeForYou == "Victory" else 0)

    stats["winratio"] = "{0:.0f}".format( (100.0 * stats["win"] / stats["total"]) if not stats["total"] == 0 else 0 )

    return render_template("history01.html", pagename="Match history", matches=matches, stats=stats, hasLess=offset != 0, hasMore=True, pageNum=offset, pageLen=PAGE_LEN)


@app.route('/decks', methods=['GET'])
def decksPage():
    decksstats = db.getDeckStats()
    deckscolors = db.getDecksColorsStats()

    #sorting (default is by weigthed wins)
    ordr = "winweight" if not "order" in request.args else request.args["order"]

    if ordr == "name":
        decksstats.sort(key=lambda x: x["DECK_NAME"].lower())
    elif ordr == "mana":
        decksstats.sort(key=lambda x: x["MANA"])
    elif ordr == "winratio":
        decksstats.sort(key=lambda x: x["WinRatioPercent"], reverse=True)
    elif ordr == "playcount":
        decksstats.sort(key=lambda x: x["TotalMatch"], reverse=True)
    elif ordr == "wincount":
        decksstats.sort(key=lambda x: x["TotalWin"], reverse=True)
    elif ordr == "winweight":
        decksstats.sort(key=lambda x: x["WeigthedRanking"], reverse=True)

    return render_template("decksstats01.html", pagename="Decks statistics", stats=decksstats, colors=deckscolors[0])



@app.route('/opponents')
def opponentsPage():
    return render_template("template01.html", pagename="Opponents", pagecontent='''TODO''')


@app.route('/settings', methods=['GET', 'POST'])
def settingsPage():
    msg = ""
    if request.method == 'POST':
        #print(str(request.form))
        if 'delete_today_btn' in request.form:
            db.deleteTodaysData()
            msg = "Deleted today's data."
        if 'reload_btn' in request.form:
            init()
            msg = "Reloaded logs."
            
    return render_template("settings.html", pagename="Settings", pagecontent=msg)

########################################################################################
## Non-web related functions
#

#---------------------------------------------------------------------------------------
# Processes 1 file (path to the file)
def scanOneFile (scanner, path):
    if db.fileAlreadyProcessed(path):
        print("INFO: Skipping already processed '%s'." % (os.path.basename(path)))
        return
    
    print ("INFO: Scanning " + path)
    mlist, goldAndGems = scanner.scanFile(path)
    for m in mlist:
        if m.deck != None:
            db.storeDeck(m.deck)
            #get the tile URL
            m.deck.tileURL = mtgalib.getImageURLFromDeck(m.deck, "small")
            db.saveDeckURL(m.deck)
        else:
            print ("WARN: match without deck => " + str(m))
        db.storeMatch(m)
    
    #and remember
    db.markFileAsProcessed(path, goldAndGems)

########################################################################################
## Main entry point
#
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print ("Need to pass the path to a MTGA log file or folder of the logs")
        exit()


    try:
        #start web interface
        app.debug = True
        app.run(host='0.0.0.0', port=45678, threaded=True)

    finally:
        pass