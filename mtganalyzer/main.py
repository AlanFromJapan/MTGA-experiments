from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, make_response
import os
import logging
from logging.handlers import RotatingFileHandler
import re
import werkzeug 
import operator
import time

import mtgalib


app = Flask(__name__, static_url_path='')

ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'ico'])


@app.route('/')
def homepage():
    return 'Hello world <img src="%s" />' % (mtgalib.getImageURLFromArenaID(78909, "small"))

########################################################################################
## Main entry point
#
if __name__ == '__main__':
    try:
        app.debug = True
        app.run(host='0.0.0.0', port=45678, threaded=True)
    finally:
        pass