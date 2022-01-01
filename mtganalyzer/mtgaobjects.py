import os
from datetime import date, datetime

class MtgaMatch:
    matchId = ""
    matchStart = datetime.min
    matchEnd = datetime.max
    opponentName = "**unknown**"
    opponentTeamId = -1
    matchOutcomeForYou = "?"
    deck = None

    def __init__(self, matchId, matchStart, opponentName, opponentTeamId, matchEnd = datetime.max, outcome="?") -> None:
        self.matchId = matchId
        self.matchStart = matchStart
        self.opponentName = opponentName
        self.opponentTeamId = opponentTeamId

        self.matchEnd = matchEnd
        self.matchOutcomeForYou = outcome
        

    def setDeck(self, d):
        self.deck = d

    def setMatchEnd(self, endTime, outcome):
        self.matchEnd = endTime
        self.matchOutcomeForYou = outcome

    def __repr__(self) -> str:
        return "Played %s at %s with deck '%s' (team #%s) with result '%s' for you. [match ID='%s']" %(self.opponentName, self.matchStart, self.deck.name if self.deck != None else "**Unknown deck**" , self.opponentTeamId, self.matchOutcomeForYou, self.matchId)

    def duration(self):
        s = datetime.strptime(self.matchStart, "%Y-%m-%d %H:%M:%S")
        e = datetime.strptime(self.matchEnd, "%Y-%m-%d %H:%M:%S")
        return e - s

class MtgaDeck:
    name = "**unnamed**"
    deckId = ""
    tileCardArenaID = -1
    mana = ""
    tileURL = None

    def __init__(self, name, tileCardId, deckId, mana, tileURL=None) -> None:
        self.name = name
        self.tileCardArenaID = tileCardId
        self.mana = mana
        self.deckId = deckId
        self.tileURL = tileURL

    def __repr__(self) -> str:
        return "Deck '%s' (%s) [tile=%s, id=%s)" %(self.name, self.mana, self.tileCardArenaID, self.deckId)
