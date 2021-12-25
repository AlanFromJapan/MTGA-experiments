##########################################################################
## Lib handling the additional functions like fetching visuals, etc. from external sources
##
## Main API: https://scryfall.com/docs/api/cards/arena
#
import requests
import json

#return the URI from an arenaid of a card and in a supported size by scryfall
def getImageURLFromArenaID (arenaId, size):
    resp = requests.get("https://api.scryfall.com/cards/arena/%s" % (arenaId))
    if resp.ok:
        j = json.loads(resp.text)
        return j["image_uris"][size]
    else:
        return "NOT-FOUND" #TODO: put a nice not found image URL here
