-- Adminer 4.2.5 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

CREATE TABLE `oferta` (
  `myid` int(16) unsigned NOT NULL AUTO_INCREMENT COMMENT 'primary key lokalnej tabeli ',
  `r_id` int(12) unsigned NOT NULL COMMENT 'raw ID oferty TSO',
  `r_senderID` int(12) unsigned NOT NULL COMMENT 'raw ID wystawiającego',
  `r_created` double unsigned NOT NULL COMMENT 'raw_TS_created_msec_Since_Epoch',
  `r_slotPos` tinyint(3) unsigned DEFAULT NULL COMMENT 'raw unknown',
  `r_slotType` tinyint(3) unsigned DEFAULT NULL COMMENT 'raw unknown',
  `r_offer` varchar(222) COLLATE utf8_unicode_ci NOT NULL COMMENT 'raw offer string',
  `r_senderName` varchar(100) COLLATE utf8_unicode_ci NOT NULL COMMENT 'raw senderName',
  `r_type` tinyint(3) unsigned DEFAULT NULL COMMENT 'raw unknown',
  `r_lotsRemaining` tinyint(3) unsigned NOT NULL COMMENT 'raw lotsRemaining',
  `realmName` varchar(100) COLLATE utf8_unicode_ci NOT NULL COMMENT 'realmName',
  `updated_ts` int(12) unsigned NOT NULL COMMENT 'updated TS(sec since epoch)',
  `created_ts` int(12) unsigned NOT NULL COMMENT 'created TS(sec since epoch)',
  `expires_ts` int(12) unsigned NOT NULL COMMENT 'expires TS(sec since epoch)',
  `co` varchar(80) COLLATE utf8_unicode_ci NOT NULL COMMENT 'oferowany towar, string',
  `za_co` varchar(80) COLLATE utf8_unicode_ci NOT NULL COMMENT 'żądany towar, string',
  `ile` int(12) unsigned NOT NULL COMMENT 'oferowana ilość, int',
  `za_ile` int(12) unsigned NOT NULL COMMENT 'żądana ilość, int',
  `oneco_eq_xzaco` double unsigned NOT NULL COMMENT 'x = ile/za_ile',
  `xco_eq_onezaco` double unsigned NOT NULL COMMENT 'x = 1 / (ile/za_ile)',
  `lots_sold` tinyint(3) unsigned NOT NULL DEFAULT '0' COMMENT 'sprzedanych transzy',
  `lots_sent` tinyint(3) unsigned NOT NULL COMMENT 'wysłanych transzy',
  `age_sec` int(12) unsigned NOT NULL COMMENT 'age_sec',
  `sold_per_hr` double unsigned NOT NULL DEFAULT '0' COMMENT 'transzy sprzedanych/godzinę',
  PRIMARY KEY (`myid`),
  UNIQUE KEY `uniklucz` (`r_id`,`r_created`,`r_lotsRemaining`,`realmName`),
  KEY `co` (`co`),
  KEY `realmName` (`realmName`),
  KEY `senderID_senderName_realmName` (`r_senderID`,`r_senderName`,`realmName`),
  KEY `zaco` (`za_co`),
  KEY `senderName` (`r_senderName`),
  FULLTEXT KEY `co_zaco_senderName` (`co`,`za_co`,`r_senderName`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci COMMENT='archiwum danych handlowych';


-- 2016-09-03 22:23:23

