-- Adminer 4.2.2 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';

CREATE TABLE `offki` (
  `myid` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT 'klucz główny tabeli',
  `raw_offerID` int(10) unsigned NOT NULL COMMENT 'ID oferty',
  `raw_senderID` int(10) unsigned NOT NULL COMMENT 'ID wysyłającego',
  `raw_senderName` varchar(60) COLLATE utf8_unicode_ci NOT NULL COMMENT 'ksywka wysyłającego',
  `raw_type` tinyint(3) unsigned NOT NULL COMMENT '0=4 transze normal itms both sides; 1=4transze sellin normal, wanted special; 2=1 transza, sellin special, wanted normal; 4=1 transza, sellin special 4 special',
  `raw_created` int(20) unsigned NOT NULL COMMENT 'seconds since epoch utworzenia',
  `raw_lotsRemaining` tinyint(3) unsigned NOT NULL COMMENT 'transzy pozostałych',
  `raw_offer` varchar(160) COLLATE utf8_unicode_ci NOT NULL COMMENT 'co&ile&zaco&zaile&transze_wyst',
  `raw_offer_transze` tinyint(3) unsigned NOT NULL COMMENT 'transzy wystawionych',
  `server_source_timestamp` int(20) unsigned NOT NULL COMMENT 'seconds since epoch pobrania danych z serwera',
  `co` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'nazwa towaru kupowanego',
  `zaCo` varchar(80) COLLATE utf8_unicode_ci DEFAULT NULL COMMENT 'nazwa towaru którym płacimy',
  `ile` int(16) unsigned DEFAULT NULL COMMENT 'ilość towaru kupowanego',
  `zaIle` int(16) unsigned DEFAULT NULL COMMENT 'ilość towaru którym płacimy',
  `ONEco_rowne_xzaco` double unsigned DEFAULT NULL COMMENT '1 sztuka co warta jest tyle sztuk zaco',
  `xco_rowne_ONEzaco` double unsigned DEFAULT NULL COMMENT '1 sztuka zaco warta jest tyle sztuk co',
  `lots_sold` tinyint(3) unsigned DEFAULT NULL COMMENT 'transz sprzedano',
  `offer_age_sec` int(20) unsigned DEFAULT NULL COMMENT 'wiek oferty w sek',
  `sold_per_hour` float unsigned NOT NULL COMMENT 'transz sprzedano / godzinę',
  `removed` bit(1) DEFAULT NULL COMMENT 'ustawiane gdy oferta znika z rynku',
  PRIMARY KEY (`myid`),
  UNIQUE KEY `offerID_senderID_lotsRemaining` (`raw_offerID`,`raw_senderID`,`raw_lotsRemaining`),
  KEY `offerID_senderID_co_zaCo_created_timestamp_senderName` (`raw_offerID`,`raw_senderID`,`co`,`zaCo`,`raw_created`,`server_source_timestamp`,`raw_senderName`)
) ENGINE=InnoDB AUTO_INCREMENT=31969 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci CHECKSUM=1 KEY_BLOCK_SIZE=64;


-- 2016-01-22 06:51:46
