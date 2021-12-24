import os
import re
import json
import sys
from datetime import datetime
import config

#------------------------------------------------------------------------------------------------------
# Shared vars & consts
SAMPLE1="/home/alan/Git/MTGA-experiments/MTGA_Logs/UTC_Log - 12-24-2021 08.05.26.log"

#RTFM https://docs.python.org/3/library/re.html
REGEX_Playername='"playerName": "(?P<name>[^"]+)"'
REGEX_Gold='"Gold\\\\\D+(?P<gold>\d+)'
REGEX_Gems='"Gems\\\\\D+(?P<gems>\d+)'
REGEX_Deckname='"Name\\\\\W+\"(?P<name>[^\\\\]+)'

rePlayername = re.compile(REGEX_Playername)
reGold = re.compile(REGEX_Gold)
reGems = re.compile(REGEX_Gems)
reDeckname = re.compile(REGEX_Deckname)

#------------------------------------------------------------------------------------------------------
# Returns the match START details: opponent, start-time, matchID, opponent team ID
#
def extractMatchStart(l):
    #use search not match since the pattern is not at the line begining
    m = rePlayername.search(l)
    if m != None:
        #found, now unpack the json message
        j = json.loads(l)

        #we are in a random team so find which one
        idx = 0        
        if config.myconfig["my_userId"] == j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["reservedPlayers"][idx]["userId"]:
            #NOT our team
            idx = 1

        opponentName = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["reservedPlayers"][idx]["playerName"]
        opponentTeam = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["reservedPlayers"][idx]["teamId"]

        tim = datetime.fromtimestamp(int(j["timestamp"][:10])) #why only first 10 chars? what are the remaining 3? no idea.
        matchID = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["matchId"]

        #print("%s %s" % (opponent, tim))
        #print(j)

        return [opponentName, tim, matchID, opponentTeam]
    else:
        return None

#------------------------------------------------------------------------------------------------------
# Returns the match END details: result, end-time, matchId
#
def extractMatchEnd(l, pMatchID, pOpponentTeamId):
    #search with quotes, that will be the json message
    if '''"MatchGameRoomStateType_MatchCompleted"''' in l:
        #found, now unpack the json message
        j = json.loads(l)
        #beware there's a nuance between the match and the game (in case of best-of-3), should deal with that here later, not always [0]
        res = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["finalMatchResult"]["resultList"][0]["winningTeamId"]
        tim = datetime.fromtimestamp(int(j["timestamp"][:10])) #why only first 10 chars? what are the remaining 3? no idea.
        matchID = j["matchGameRoomStateChangedEvent"]["gameRoomInfo"]["gameRoomConfig"]["matchId"]

        if matchID != pMatchID:
            print("Wrong match: expect %s found %s" % (pMatchID, matchID))
            return None
        #print(j)

        #which team was the winner?
        if int(res) == int(pOpponentTeamId):
            res = "Defeat"
        else:
            res = "Victory"

        return [res, tim, matchID]
    else:
        return None


#------------------------------------------------------------------------------------------------------
# Returns Gold and Gems (could do also the wildcards, in the same message)
#
def extractGoldAndGems(l):
    if "SealedTokens" in l and "1909" in l:
        #print ("DBG: " + l)
        go = -1
        ge = -1

        #using 2 separate regex, not sure they are always in same order in the message
        m = reGold.search(l)
        if m != None:
            #print ("DBG: MATCH! => " + m.group("gold") )
            go = m.group("gold")

        m = reGems.search(l)
        if m != None:
            #print ("DBG: MATCH! => " + m.group("gold") )
            ge = m.group("gems")

        return [go, ge]
    return None


#------------------------------------------------------------------------------------------------------
# Returns Last deck set (normally the one used) 
#
def extractUsedDeck(l):
    if "Event_SetDeck" in l and ":602" in l:
        m = reDeckname.search(l)
        #print("DBG: found deck named " + m.group("name"))
        return m.group("name")
        
    return None

#######################################################################################################
##                                                                                                   ##
##                                     M A I N                                                       ##
##                                                                                                   ##
#######################################################################################################
if len(sys.argv) == 1:
    print ("Need to pass the path to a MTGA log file")
    exit()

print ("My user id " + config.myconfig["my_userId"])

fin = open(str(sys.argv[1]), "rt")

STATE_START = "MATCH_START"
STATE_END = "MATCH_END"
#state machine: file is sequential (it's a log) so "what are we searching for" phases state machine
#not pairing the matches (checking ID assuming that all started match are properly finished : will have to fix that later)
stateMachine = STATE_START
try:
    i = 1

    lastMatch = ""
    lastOpponentTeam = 0
    lastGoldAndGem = None
    lastDeck = None

    while True:
        l = fin.readline()
        if not l:
            break

        if stateMachine == STATE_START:
            de = extractUsedDeck(l)
            if de != None:
                lastDeck = de

            match = extractMatchStart(l)
            if match != None:            
                print("line %d: Played %s at %s with deck '%s' (team #%s)" %(i,match[0], match[1], lastDeck, match[3] ))
                lastMatch = match[2]
                lastOpponentTeam = match[3]
                stateMachine = STATE_END
        elif stateMachine == STATE_END:
            match = extractMatchEnd(l, lastMatch, lastOpponentTeam)
            if match != None:            
                print("line %d: %s at %s" %(i,match[0], match[1]))
                stateMachine = STATE_START

        gng = extractGoldAndGems(l)
        if gng != None:
            lastGoldAndGem = gng
        #loop
        i = i + 1
    
    if lastGoldAndGem != None:
        print("Closing Gold = %s, Gems = %s" % (lastGoldAndGem[0], lastGoldAndGem[1]))
    print("Finished.")
finally:
    fin.close()

