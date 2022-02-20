##########################################################################
## Lib handling the LOGS file parsing and defining base objects
#
import os
from datetime import datetime
import re
import json
import sys
import db

from mtgaobjects import MtgaDeck, MtgaMatch, BLANK_TILE, SIZE_TILE
import mtgalib
        


class MtgaLogScanner:
    #------------------------------------------------------------------------------------------------------
    # Shared vars & consts
    myPlayerId =""

    #RTFM https://docs.python.org/3/library/re.html
    REGEX_Playername='"playerName": "(?P<name>[^"]+)"'
    REGEX_Gold='"Gold\\\\\D+(?P<gold>\d+)'
    REGEX_Gems='"Gems\\\\\D+(?P<gems>\d+)'

    REGEX_Deckname='"Name\\\\\W+\"(?P<name>[^\\\\]+)'
    REGEX_Decktile='"DeckTileId\\\\\D+(?P<id>\d+)'
    REGEX_DeckId='"DeckId\\\\\W+\"(?P<id>[^\\\\]+)'
    REGEX_DeckMana='"Mana\\\\\W+\"(?P<mana>[^\\\\]+)'
    

    rePlayername = re.compile(REGEX_Playername)
    reGold = re.compile(REGEX_Gold)
    reGems = re.compile(REGEX_Gems)
    reDeckname = re.compile(REGEX_Deckname)
    reDecktile = re.compile(REGEX_Decktile)
    reDeckId = re.compile(REGEX_DeckId)
    reDeckMana = re.compile(REGEX_DeckMana)



    #------------------------------------------------------------------------------------------------------
    # Constructor: pass your player ID
    #
    def __init__(self, playerId):
        self.myPlayerId = playerId


    #------------------------------------------------------------------------------------------------------
    # Returns the match START details: opponent, start-time, matchID, opponent team ID
    #
    def extractMatchStart(self, l):
        #use search not match since the pattern is not at the line begining
        m = self.rePlayername.search(l)
        if m != None:
            #found, now unpack the json message
            j = json.loads(l)

            #we are in a random team so find which one
            idx = 0        
            if self.myPlayerId == j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["reservedPlayers"][idx]["userId"]:
                #NOT our team
                idx = 1

            opponentName = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["reservedPlayers"][idx]["playerName"]
            opponentTeam = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["reservedPlayers"][idx]["teamId"]

            tim = datetime.fromtimestamp(int(j["timestamp"][:10])) #why only first 10 chars? what are the remaining 3? no idea.
            matchID = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["matchId"]

            #print("%s %s" % (opponent, tim))
            #print(j)

            #return [opponentName, tim, matchID, opponentTeam]
            return MtgaMatch(matchID, tim, opponentName, opponentTeam)
        else:
            return None

    #------------------------------------------------------------------------------------------------------
    # Returns the match END details: result, end-time, matchId
    #
    def extractMatchEnd(self, l, match : MtgaMatch):
        #search with quotes, that will be the json message
        if '''"MatchGameRoomStateType_MatchCompleted"''' in l:
            #found, now unpack the json message
            j = json.loads(l)
            #beware there's a nuance between the match and the game (in case of best-of-3), should deal with that here later, not always [0]
            res = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["finalMatchResult"]["resultList"][0]["winningTeamId"]
            tim = datetime.fromtimestamp(int(j["timestamp"][:10])) #why only first 10 chars? what are the remaining 3? no idea.
            matchID = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["matchId"]

            if matchID != match.matchId:
                print("Wrong match: expect %s found %s" % (match.matchId, matchID))
                return None
            #print(j)

            #which team was the winner?
            if int(res) == int(match.opponentTeamId):
                res = "Defeat"
            else:
                res = "Victory"

            #return [res, tim, matchID]
            match.setMatchEnd(tim, res)
            return match
        else:
            return None


    #------------------------------------------------------------------------------------------------------
    # Returns Gold and Gems (could do also the wildcards, in the same message)
    #
    def extractGoldAndGems(self, l):
        if "SealedTokens" in l and "1912" in l:
            #print ("DBG: " + l)
            go = -1
            ge = -1

            #using 2 separate regex, not sure they are always in same order in the message
            m = self.reGold.search(l)
            if m != None:
                #print ("DBG: MATCH! => " + m.group("gold") )
                go = m.group("gold")

            m = self.reGems.search(l)
            if m != None:
                #print ("DBG: MATCH! => " + m.group("gold") )
                ge = m.group("gems")

            return [go, ge]
        return None


    #------------------------------------------------------------------------------------------------------
    # Returns Last deck set (normally the one used) 
    #
    def extractUsedDeck(self, l):
        if "Deck_UpsertDeck" in l and ":402" in l:
            m = self.reDeckname.search(l)
            m2 = self.reDecktile.search(l)
            m3 = self.reDeckId.search(l)
            m4 = self.reDeckMana.search(l)
            #print("DBG: found deck named " + m.group("name"))
            d = MtgaDeck(m.group("name"), m2.group("id"), m3.group("id"), m4.group("mana"))
            #print ("DBG: deck " + str(d))
            return d

        return None


    #------------------------------------------------------------------------------------------------------
    # Scans a file and return the list of matches and otehr info
    #
    def scanFile(self, fileName):
        mlist = []

        fin = open(fileName, "rt")

        STATE_START = "MATCH_START"
        STATE_END = "MATCH_END"
        lastGoldAndGem = None

        #state machine: file is sequential (it's a log) so "what are we searching for" phases state machine
        #not pairing the matches (checking ID assuming that all started match are properly finished : will have to fix that later)
        stateMachine = STATE_START
        try:
            i = 1

            lastDeck = None
            lastMatch = None

            while True:
                l = fin.readline()
                if not l:
                    break

                if stateMachine == STATE_START:
                    de = self.extractUsedDeck(l)
                    if de != None:
                        lastDeck = de

                    lastMatch = self.extractMatchStart(l)
                    if lastMatch != None:            
                        lastMatch.deck = lastDeck
                        #print("line %d: %s" %(i,lastMatch))
                        stateMachine = STATE_END
                elif stateMachine == STATE_END:
                    res = self.extractMatchEnd(l, lastMatch)
                    if res != None:      
                        #found a match, so overwrite lastOne      
                        lastMatch = res
                        #print("line %d: %s" %(i,lastMatch))

                        mlist.append(lastMatch)

                        #and reset
                        lastMatch = None
                        lastDeck = None
                        stateMachine = STATE_START

                gng = self.extractGoldAndGems(l)
                if gng != None:
                    lastGoldAndGem = gng
                #loop
                i = i + 1
            
            if lastGoldAndGem != None:
                print("Closing Gold = %s, Gems = %s" % (lastGoldAndGem[0], lastGoldAndGem[1]))
            print("Finished.")
        finally:
            fin.close()

        return mlist, lastGoldAndGem


    #------------------------------------------------------------------------------------------------------
    # Refresh (attempts to) the tiles images from Scryfall for Decks with the generic blank image
    #
    def refreshDeckMissingTiles(self):
        decks = db.getDeckStats ()
        for deck in decks:
            if deck["TILE_URL_SMALL"] == BLANK_TILE:
                print("DBG: processing deck ID '"+ deck["DECK_NAME"] + "' with Tile ID " + deck["TILE_ARENAID"])
                imgURL = mtgalib.getImageURLFromArenaID(deck["TILE_ARENAID"], SIZE_TILE)
                if imgURL != BLANK_TILE:
                    print("DBG: got a new URL "+ imgURL)
                    d = MtgaDeck(None, None, None, None)
                    d.deckId = deck["DECK_ID"]
                    d.tileURL = imgURL
                    db.saveDeckTileURL(d)
                else:
                    print("WARN: could not find new image for deck ID '"+ deck["DECK_NAME"] + "' with Tile ID " + deck["TILE_ARENAID"])


