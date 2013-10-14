--
-- TOT Database Schema
-- Ver 1.0
-- Aug 9. 2013
--

CREATE DATABASE IF NOT EXISTS tot_db;

SET SESSION storage_engine = "InnoDB";
SET SESSION time_zone = "+0:00";
ALTER DATABASE CHARACTER SET "utf8";

-- Table: user info --
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    uid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    uname VARCHAR(100) NOT NULL,
    passcode VARCHAR(512) NOT NULL
);

DROP TABLE IF EXISTS entries;
CREATE TABLE entries (
    eid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    uid INT NOT NULL REFERENCES users(uid),
    entry VARCHAR(1024) NOT NULL,
    published DATETIME NOT NULL
);

DROP TABLE IF EXISTS ForgetPasswordUsers;
CREATE TABLE ForgetPasswordUsers (
    email VARCHAR(100) NOT NULL UNIQUE PRIMARY KEY REFERENCES users(email),
    PasswordResetToken VARCHAR(1024) NOT NULL,
    PasswordResetExpiration DATETIME NOT NULL
);
