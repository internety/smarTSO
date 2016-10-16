CREATE TABLE pid_name_realm_map (
    id  INTEGER      PRIMARY KEY AUTOINCREMENT,
    pN  VARCHAR (64) NOT NULL,
    pID INT          NOT NULL,
    rN  VARCHAR (32) NOT NULL,
    CONSTRAINT uniqa UNIQUE (
        pN COLLATE NOCASE,
        pID,
        rN COLLATE NOCASE
    )
    ON CONFLICT IGNORE
);

