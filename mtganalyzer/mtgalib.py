from mtgaobjects import MtgaDeck, MtgaMatch, BLANK_TILE

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
            #print("DBG: "+ resp.text)
            if "image_uris" in j:
                #single face card
                #print ("DBG: single face")
                cache_ArenaID2ImageURL[arenaId] = j["image_uris"][size]
            else:
                #multi face cards
                #print ("DBG: multi face")
                cache_ArenaID2ImageURL[arenaId] = j["card_faces"][0]["image_uris"][size]
            return cache_ArenaID2ImageURL[arenaId]
        else:
            return BLANK_TILE 
    except:
        print ("WARN: couldn't get tile URL for ArenaID %s" % (arenaId))
        return BLANK_TILE



#return the URI from an arenaid of a card and in a supported size by scryfall
def getImageURLFromDeck (d: MtgaDeck , size):
    return getImageURLFromArenaID(d.tileCardArenaID, size)