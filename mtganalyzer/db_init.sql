--Script to generate the DB structure (sqlite)

CREATE TABLE PROCESSING_HISTORY (
    FILE_NAME VARCHAR(100) PRIMARY KEY NOT NULL,
    PROCESS_DT DATETIME NOT NULL
);


CREATE TABLE DECK (
    DECK_ID varchar(120) PRIMARY KEY NOT NULL,
    DECK_NAME nvarchar(120) NOT NULL,
    MANA varchar(10) NULL,
    TILE_ARENAID varchar(50) NULL
);

CREATE TABLE MATCH (
    MATCH_ID varchar(120) PRIMARY KEY NOT NULL,
    OPPONENT_NAME nvarchar(100),
    OPPONENT_ID varchar(120),
    RESULT varchar(20),
    MATCH_START DATETIME,
    MATCH_END DATETIME,
    DECK_ID varchar(120) NULL,

    FOREIGN KEY(DECK_ID) REFERENCES DECK(DECK_ID)
);

