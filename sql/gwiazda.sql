-- Adminer 4.2.4 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';

CREATE TABLE `gwiazda` (
  `myid` int(16) unsigned NOT NULL AUTO_INCREMENT,
  `playerID` int(12) unsigned NOT NULL,
  `playerName` varchar(60) COLLATE utf8_unicode_ci NOT NULL,
  `amount` int(12) unsigned NOT NULL,
  `buffName_string` varchar(80) COLLATE utf8_unicode_ci NOT NULL,
  `resourceName_string` varchar(80) COLLATE utf8_unicode_ci NOT NULL,
  `kiedyZlapanoTS` int(12) unsigned NOT NULL,
  PRIMARY KEY (`myid`),
  FULLTEXT KEY `resourceName_string_buffName_string_playerName` (`resourceName_string`,`buffName_string`,`playerName`)
) ENGINE=InnoDB AUTO_INCREMENT=65017 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


-- 2016-09-17 15:35:39