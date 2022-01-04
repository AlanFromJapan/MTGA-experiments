from mtgaobjects import MtgaDeck, MtgaMatch

##########################################################################
## Lib handling the additional functions like fetching visuals, etc. from external sources
##
## Main API: https://scryfall.com/docs/api/cards/arena
#
import requests
import json
import time


cache_ArenaID2ImageURL = {}

#return the URI from an arenaid of a card and in a supported size by scryfall
def getImageURLFromArenaID (arenaId, size):
    global cache_ArenaID2ImageURL

    #check the cache first
    if arenaId in cache_ArenaID2ImageURL:
        #print ("DBG: URL found tile in cache %s -> %s" % (arenaId, cache_ArenaID2ImageURL[arenaId]))
        return cache_ArenaID2ImageURL[arenaId]

    #not in cache
    try:
        #print ("DBG: URL NOT found tile in cache %s" % (arenaId))
        resp = requests.get("https://api.scryfall.com/cards/arena/%s" % (arenaId))
        #Scryfall asked to not flood their service
        time.sleep(0.1)

        if resp.ok:
            j = json.loads(resp.text)
            cache_ArenaID2ImageURL[arenaId] = j["image_uris"][size]
            return cache_ArenaID2ImageURL[arenaId]
        else:
            return "/images/blank-card.png" 
    except:
        print ("WARN: couldn't get tile URL for ArenaID %s" % (arenaId))
        return "/images/blank-card.png" 



#return the URI from an arenaid of a card and in a supported size by scryfall
def getImageURLFromDeck (d: MtgaDeck , size):
    return getImageURLFromArenaID(d.tileCardArenaID, size)