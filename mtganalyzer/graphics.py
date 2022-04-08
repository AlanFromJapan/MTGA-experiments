from random import random
from PIL import Image, ImageDraw
import db

BAR_W=5
BAR_H_UNIT=5

DAYS_COUNT=20

HIST_W=(BAR_W + 1) * DAYS_COUNT + BAR_W *2 #padding L/R
HIST_H=50

IMG_W=HIST_W + 10
IMG_H=HIST_H + 10

def generateDeckHistory (deckID:str, historyWinLoss):
    #histo = db.getDeckWinlossHistory(deckID=deckID)

    img = Image.new('RGB', (IMG_W, IMG_H), color = 'darkgrey')

    maxBars = int(HIST_W / BAR_W)


    d = ImageDraw.Draw(img)
    d.line(((IMG_W - HIST_W) /2, IMG_H/2, IMG_W - ((IMG_W - HIST_W) /2), IMG_H/2), fill=(220,220,220), width=1)

    l = (IMG_W - HIST_W) /2
    l = l + BAR_W * (0 if len(historyWinLoss) >= DAYS_COUNT else DAYS_COUNT- len(historyWinLoss) )

    for triplet in historyWinLoss[-DAYS_COUNT:]:
        if triplet["VictoryCount"] > 0:
            d.rectangle( (l, IMG_H/2 - BAR_H_UNIT * triplet["VictoryCount"], l + BAR_W, IMG_H/2), 
            fill=(70,70,255),
            outline=None )
        if triplet["DefeatCount"] > 0:
            d.rectangle( (l, IMG_H/2 + BAR_H_UNIT * triplet["DefeatCount"], l + BAR_W, IMG_H/2), 
            fill=(255,70,70),
            outline=None )   
        l = l + BAR_W + 2

    #d.text((10,10), "Hello World", fill=(255,0,0))

    return img