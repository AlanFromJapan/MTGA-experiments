##########################################################################
## Lib handling the LOGS file parsing and defining base objects
#
import os
from datetime import datetime

class MtgaMatch:
    matchId = ""
    matchStart = datetime.min
    matchEnd = datetime.max
    opponentName = "**unknown**"
    opponentTeamId = -1
    matchOutcomeForYou = ""


class MtgaDeck:
    name = "**unnamed**"
    titleCardArenaID = -1
    totalWins = -1
    totalLoss = -1


