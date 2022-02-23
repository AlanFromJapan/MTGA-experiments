from random import random
from PIL import Image, ImageDraw
import db

IMG_W=200
IMG_H=100

HIST_W=180
HIST_H=90

BAR_W=3

def generateDeckHistory (deckID:str):
    #histo = db.getDeckWinlossHistory(deckID=deckID)

    img = Image.new('RGB', (IMG_W, IMG_H), color = 'white')

    maxBars = int(HIST_W / BAR_W)


    d = ImageDraw.Draw(img)
    d.line(((IMG_W - HIST_W) /2, IMG_H/2, IMG_W - ((IMG_W - HIST_W) /2), IMG_H/2), fill=(220,220,220), width=1)

    l = (IMG_W - HIST_W) /2
    for i in range(1, maxBars):
        d.rectangle( (l + (i-1) * BAR_W, IMG_H/2 - 10 + 20* random(), l + (i) * BAR_W, IMG_H/2), 
        fill=(70,70,255),
        outline=None )

    d.text((10,10), "Hello World", fill=(255,0,0))

    return img