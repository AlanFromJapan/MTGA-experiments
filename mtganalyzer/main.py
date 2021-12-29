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



app = Flask(__name__, static_url_path='')

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ico'])


@app.route('/')
def homepage():
    return 'Hello world <img src="%s" />' % (mtgalib.getImageURLFromArenaID(78909, "small"))

########################################################################################
## Non-web related functions
#

#---------------------------------------------------------------------------------------
# Processes 1 file (path to the file)
def scanOneFile (path):
    print ("Scanning " + path)
    mlist = scanner.scanFile(path)
    for m in mlist:
        db.storeMatch(m)

########################################################################################
## Main entry point
#
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print ("Need to pass the path to a MTGA log file or folder of the logs")
        exit()


    #Init
    myPlayerId = config.myconfig["my_userId"]
    print ("My user id " + myPlayerId)

    try:
        #DB setup
        #db.deleteDB()
        db.initDB()
 
        #scanner init
        scanner = mtgalogs.MtgaLogScanner(myPlayerId)

        #scan 
        paramPath = str(sys.argv[1])
        if ".log" == paramPath[-4:].lower():
            #scan 1 file
            scanOneFile(paramPath)
        else:
            #assume it's a folder
            for f in os.listdir(paramPath):
                scanOneFile(os.path.join(paramPath, f))

        #start web interface
        app.debug = True
        app.run(host='0.0.0.0', port=45678, threaded=True)

    finally:
        pass