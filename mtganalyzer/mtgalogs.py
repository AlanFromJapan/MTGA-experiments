##########################################################################
## Lib handling the LOGS file parsing and defining base objects
#
import os
from datetime import datetime
import re
import json
import sys


class MtgaMatch:
    matchId = ""
    matchStart = datetime.min
    matchEnd = datetime.max
    opponentName = "**unknown**"
    opponentTeamId = -1
    matchOutcomeForYou = "?"
    deck = None

    def __init__(self, matchId, matchStart, opponentName, opponentTeamId) -> None:
        self.matchId = matchId
        self.matchStart = matchStart
        self.opponentName = opponentName
        self.opponentTeamId = opponentTeamId

    def setDeck(self, d):
        self.deck = d

    def setMatchEnd(self, endTime, outcome):
        self.matchEnd = endTime
        self.matchOutcomeForYou = outcome

    def __repr__(self) -> str:
        return "Played %s at %s with deck '%s' (team #%s) with result '%s' for you. [match ID='%s']" %(self.opponentName, self.matchStart, self.deck if self.deck != None else "**Unknown deck**" , self.opponentTeamId, self.matchOutcomeForYou, self.matchId)


class MtgaDeck:
    name = "**unnamed**"
    tileCardArenaID = -1
    totalWins = -1
    totalLoss = -1

    def __init__(self, name, tileCardId) -> None:
        self.name = name
        self.tileCardArenaID = tileCardId
        


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
    

    rePlayername = re.compile(REGEX_Playername)
    reGold = re.compile(REGEX_Gold)
    reGems = re.compile(REGEX_Gems)
    reDeckname = re.compile(REGEX_Deckname)
    reDecktile = re.compile(REGEX_Decktile)



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
        if "SealedTokens" in l and "1909" in l:
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
        if "Event_SetDeck" in l and ":602" in l:
            m = self.reDeckname.search(l)
            m2 = self.reDecktile.search(l)
            #print("DBG: found deck named " + m.group("name"))
            d = MtgaDeck(m.group("name"), m2.group("id"))
            return d

        return None


    #------------------------------------------------------------------------------------------------------
    # Scans a file and return the list of matches and otehr info
    #
    def scanFile(self, fileName):
        fin = open(fileName, "rt")

        STATE_START = "MATCH_START"
        STATE_END = "MATCH_END"
        #state machine: file is sequential (it's a log) so "what are we searching for" phases state machine
        #not pairing the matches (checking ID assuming that all started match are properly finished : will have to fix that later)
        stateMachine = STATE_START
        try:
            i = 1

            lastGoldAndGem = None
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
                        print("line %d: %s" %(i,lastMatch))
                        stateMachine = STATE_END
                elif stateMachine == STATE_END:
                    res = self.extractMatchEnd(l, lastMatch)
                    if res != None:      
                        #found a match, so overwrite lastOne      
                        lastMatch = res
                        print("line %d: %s" %(i,lastMatch))

                        #and reset
                        lastMatch = None
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

