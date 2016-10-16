-- Adminer 4.2.4 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';

CREATE DATABASE `smartso` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci */;
USE `smartso`;

CREATE TABLE `auth` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `x_playername` varchar(64) COLLATE utf8_unicode_ci NOT NULL COMMENT 'XMPP - nazwa gracza',
  `x_playerid` int(10) unsigned NOT NULL COMMENT 'XMPP - ID gracza',
  `x_playertag` varchar(64) COLLATE utf8_unicode_ci NOT NULL COMMENT 'XMPP - gildia gracza',
  `x_server` varchar(64) COLLATE utf8_unicode_ci NOT NULL COMMENT 'XMPP serwer czatu ',
  `x_key` varchar(36) COLLATE utf8_unicode_ci NOT NULL COMMENT 'XMPP klucz unikat',
  `x_ts` int(14) unsigned NOT NULL COMMENT 'XMPP timestamp klucza',
  PRIMARY KEY (`id`),
  UNIQUE KEY `playername_playerid_server` (`x_playername`,`x_playerid`,`x_server`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


-- 2016-10-16 03:22:52
