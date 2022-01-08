DROP TABLE IF EXISTS tmpStats;

CREATE TEMPORARY TABLE tmpStats AS
SELECT 
    "Your most played opponent was " || OPPONENT_NAME || " with " || CAST(count(Opponent_name) as varchar(10)) || " match(es)." as OneLiner, 
    "MostPlayedDeck" as Item, 
    OPPONENT_NAME as Val, 
    count(Opponent_name) as cnt  
FROM MATCH m GROUP by OPPONENT_NAME order by count(Opponent_name) DESC LIMIT 1
;
INSERT INTO tmpStats
SELECT 
    "Your most played deck is '" || DECK_NAME || "' which you played " || count(m.DECK_ID) || " time(s)." as OneLiner, 
    "MostPlayedDeck" as Item, 
    DECK_NAME as Val, 
    count(m.DECK_ID) as cnt 
from MATCH m join DECK d on m.DECK_ID = d.DECK_ID GROUP by m.deck_id order by count(m.deck_id) desc LIMIT 1
;
INSERT INTO tmpStats
SELECT 
    "Your most winning deck is '" || DECK_NAME || "' which was victorious " || count(m.DECK_ID) || " time(s)." as OneLiner, 
    "MostWinningDeck" as Item, 
    DECK_NAME as Val, 
    count(m.DECK_ID) as cnt 
from MATCH m join DECK d on m.DECK_ID = d.DECK_ID where m.RESULT = "Victory" GROUP by m.deck_id order by count(m.deck_id) desc LIMIT 1
;
INSERT INTO tmpStats
SELECT 
    "Your average match length is " || printf("%d", avg(strftime('%s', m.MATCH_END) - strftime('%s', m.MATCH_START))) || " seconds." as OneLiner, 
    "AvgMatchLenSec" as Item, 
    CAST(avg(strftime('%s', m.MATCH_END) - strftime('%s', m.MATCH_START))  as varchar(10)), 
    0 as cnt 
from MATCH m 
;
SELECT * FROM tmpStats;



