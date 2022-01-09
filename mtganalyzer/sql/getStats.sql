DROP TABLE IF EXISTS tmpStats;

CREATE TEMPORARY TABLE tmpStats AS
SELECT 
    "Your most played non-bot opponent was <span class='generalstatsHighlight'>" || OPPONENT_NAME || "</span> with <span class='generalstatsHighlight'>" || CAST(count(Opponent_name) as varchar(10)) || "</span> match(es)." as OneLiner, 
    "MostPlayedDeck" as Item, 
    OPPONENT_NAME as Val, 
    count(Opponent_name) as cnt  
FROM MATCH m 
WHERE m.OPPONENT_NAME != "Sparky"
GROUP by OPPONENT_NAME order by count(Opponent_name) DESC LIMIT 1
;
INSERT INTO tmpStats
SELECT 
    "You played the Sparky bot <span class='generalstatsHighlight'>"  || CAST(count(Opponent_name) as varchar(10)) || "</span> time(s)." as OneLiner, 
    "MostPlayedDeck" as Item, 
    OPPONENT_NAME as Val, 
    count(Opponent_name) as cnt  
FROM MATCH m 
WHERE m.OPPONENT_NAME = "Sparky"
GROUP by OPPONENT_NAME order by count(Opponent_name) DESC LIMIT 1
;
INSERT INTO tmpStats
SELECT 
    "Your most played deck ever is '<span class='generalstatsHighlight'>" || DECK_NAME || "</span>' which you played <span class='generalstatsHighlight'>" || count(m.DECK_ID) || "</span> time(s)." as OneLiner, 
    "MostPlayedDeck" as Item, 
    DECK_NAME as Val, 
    count(m.DECK_ID) as cnt 
from MATCH m join DECK d on m.DECK_ID = d.DECK_ID GROUP by m.deck_id order by count(m.deck_id) desc LIMIT 1
;
INSERT INTO tmpStats
SELECT 
    "Your most winning deck is '<span class='generalstatsHighlight'>" || DECK_NAME || "</span>' which was victorious <span class='generalstatsHighlight'>" || count(m.DECK_ID) || "</span> time(s)." as OneLiner, 
    "MostWinningDeck" as Item, 
    DECK_NAME as Val, 
    count(m.DECK_ID) as cnt 
from MATCH m join DECK d on m.DECK_ID = d.DECK_ID where m.RESULT = "Victory" GROUP by m.deck_id order by count(m.deck_id) desc LIMIT 1
;
INSERT INTO tmpStats
SELECT 
    "Your average match length is <span class='generalstatsHighlight'>" || printf("%d", avg(strftime('%s', m.MATCH_END) - strftime('%s', m.MATCH_START))) || "</span> seconds." as OneLiner, 
    "AvgMatchLenSec" as Item, 
    CAST(avg(strftime('%s', m.MATCH_END) - strftime('%s', m.MATCH_START))  as varchar(10)), 
    0 as cnt 
from MATCH m 
;
INSERT INTO tmpStats
SELECT 
    "Your recent win ratio is <span class='generalstatsHighlight'>" || printf("%d", CAST(100.0 * SUM(case when X.RESULT = "Victory" THEN 1 ELSE 0 end) as float) / CAST(count(1) as float)) || "%</span> over the last " || cast(count(1) as varchar(10)) || " matches." as OneLiner,
    "RecentWinRatio" as Item,
    SUM(case when X.RESULT = "Victory" THEN 1 ELSE 0 end) as Val,
    0 as cnt
FROM 
(SELECT *
from MATCH m 
WHERE DECK_ID IS NOT NULL
order by m. MATCH_START desc LIMIT 10) as X
;
INSERT INTO tmpStats
SELECT 
    "Your recently favorite deck is '<span class='generalstatsHighlight'>" || d.DECK_NAME || "</span>' with <span class='generalstatsHighlight'>" || cast(count(1) as varchar(10)) || "</span> recent games over last 10." as OneLiner,
    "RecentFavoriteDeck" as Item,
    0 as Val,
    0 as cnt
FROM 
	(SELECT * FROM MATCH WHERE DECK_ID IS NOT NULL ORDER BY MATCH_START DESC LIMIT 10) as m
	join DECK d on m.DECK_ID = d.DECK_ID GROUP by m.deck_id order by count(m.deck_id) desc LIMIT 1
;
-- Final SELECT to return the results
SELECT * FROM tmpStats;



