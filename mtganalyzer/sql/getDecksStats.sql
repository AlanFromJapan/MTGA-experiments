DROP TABLE IF EXISTS TMPDECKSTATS;

CREATE TEMPORARY TABLE TMPDECKSTATS AS
select d.*, 
(SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id) as TotalMatch,
(SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id AND m.RESULT = "Victory") as TotalWin,
(SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id AND m.RESULT = "Defeat") as TotalLoss,
printf("%d", (SELECT AVG(strftime('%s', m.MATCH_END) - strftime('%s', m.MATCH_START)) FROM MATCH m WHERE m.deck_id = d.deck_id)) as AvgMatchLengthInSec,
COALESCE(CAST(100.00 * (1.00 * (SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id AND m.RESULT = "Victory")) / (1.00 * (SELECT COUNT(1) FROM MATCH m WHERE m.deck_id = d.deck_id)) as int), 0) as WinRatioPercent,
0 as WeigthedRanking
from DECK d ;

UPDATE TMPDECKSTATS SET  WeigthedRanking = TotalMatch * WinRatioPercent; 

SELECT * FROM TMPDECKSTATS ORDER BY WeigthedRanking DESC, WinRatioPercent DESC;