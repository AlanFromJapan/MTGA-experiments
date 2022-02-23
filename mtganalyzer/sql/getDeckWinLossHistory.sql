DROP TABLE IF EXISTS tmpStats;

CREATE TEMPORARY TABLE tmpStats AS
SELECT 
	strftime('%Y-%m-%d', m.MATCH_START) as TheDay, 
	SUM (case when RESULT = "Victory" THEN 1 ELSE 0 END) as VictoryCount, 
	SUM (case when RESULT = "Defeat" THEN 1 ELSE 0 END) as DefeatCount
FROM
	MATCH m
WHERE 
    --@@ params are NOT the official sqlite params but some cooking I do to use scripts AND params (see __executeScriptAndReturn())
    --so make sure to surround it with quotes if needed
	m.DECK_ID = "@@DeckID"
GROUP BY strftime('%Y-%m-%d', m.MATCH_START)
ORDER BY TheDay;


-- Final SELECT to return the results
SELECT * FROM tmpStats;
