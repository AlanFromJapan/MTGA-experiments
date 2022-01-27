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

    return render_template("home01.html", pagename="MTGAnalyzer - home", stats=stats) # dbg=stats)



@app.route('/about')
def aboutPage():
    return render_template("template01.html", pagename="MTGAnalyzer - About", pagecontent='''
About MTGAnalyzer<br/>
<br/>
By AlanFromJapan / MIT license / Full source code here <a href="https://github.com/AlanFromJapan/MTGA-experiments">on Github</a>.<br/>
This application is not approved nor affiliated with WotC or Hasbro or anyone.<br/>
Don't sue me, go play MtGA instead.
    ''')



@app.route('/matchhistory')
def matchHistoryPage():
    matches = db.getMatchLatest(100)
    stats = dict()
    stats["total"] = 0
    stats["win"] = 0

    for m in matches:
        stats["total"] = stats["total"] +1
        stats["win"] = stats["win"] + (1 if m.matchOutcomeForYou == "Victory" else 0)

    stats["winratio"] = "{0:.0f}".format( (100.0 * stats["win"] / stats["total"]) if not stats["total"] == 0 else 0 )

    return render_template("history01.html", pagename="MTGAnalyzer - match history", matches=matches, stats=stats)


@app.route('/decks')
def decksPage():
    decksstats = db.getDeckStats()
    deckscolors = db.getDecksColorsStats()

    return render_template("decksstats01.html", pagename="MTGAnalyzer - decks statistics", stats=decksstats, colors=deckscolors[0])



@app.route('/opponents')
def opponentsPage():
    return render_template("template01.html", pagename="MTGAnalyzer - About", pagecontent='''TODO''')


@app.route('/settings')
def settingsPage():
    return render_template("template01.html", pagename="MTGAnalyzer - About", pagecontent='''TODO''')

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
    mlist = scanner.scanFile(path)
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
    db.markFileAsProcessed(path)

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