DROP TABLE IF EXISTS tmpStats;

CREATE TEMPORARY TABLE tmpStats AS
SELECT
	(SELECT count(1) from DECK d WHERE d.MANA LIKE "%R%") as Reds,
	(SELECT count(1) from DECK d WHERE d.MANA LIKE "%G%") as Greens,
	(SELECT count(1) from DECK d WHERE d.MANA LIKE "%W%") as Whites,
	(SELECT count(1) from DECK d WHERE d.MANA LIKE "%U%") as Blues,
	(SELECT count(1) from DECK d WHERE d.MANA LIKE "%B%") as Blacks
;
-- Final SELECT to return the results
SELECT * FROM tmpStats;



