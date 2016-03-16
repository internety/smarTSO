-- Adminer 4.2.2 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';

CREATE TABLE `offstats` (
  `statID` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `server_source_timestamp` int(20) unsigned NOT NULL COMMENT 'timestamp danych źródłowych',
  `resource` varchar(80) COLLATE utf8_unicode_ci NOT NULL COMMENT 'nazwa produktu',
  `max_price_skup` double unsigned NOT NULL COMMENT 'max cena skupu',
  `max_price_skup_sold` double unsigned NOT NULL COMMENT '_sold = tylko sprzedane',
  `max_price_sprzed` double unsigned NOT NULL COMMENT 'max cena sprzedaży',
  `max_price_sprzed_sold` double unsigned NOT NULL COMMENT '_sold = tylko sprzedane',
  `avg_price_skup` double unsigned NOT NULL COMMENT 'średnia cena skupu',
  `avg_price_skup_sold` double unsigned NOT NULL COMMENT '_sold = tylko sprzedane',
  `avg_price_sprzed` double unsigned NOT NULL COMMENT 'średnia cena sprzedaży',
  `avg_price_sprzed_sold` double unsigned NOT NULL COMMENT '_sold = tylko sprzedane',
  `avg_sold_per_hour` double unsigned NOT NULL COMMENT 'śr. ilość sprzedaży na godzinę',
  `min_price_skup` double unsigned NOT NULL COMMENT 'min cena skupu',
  `min_price_skup_sold` double unsigned NOT NULL COMMENT '_sold = tylko sprzedane',
  `min_price_sprzed` double unsigned NOT NULL COMMENT 'min cena sprzedaży',
  `min_price_sprzed_sold` double unsigned NOT NULL COMMENT '_sold = tylko sprzedane',
  `prices_measured_in` varchar(80) COLLATE utf8_unicode_ci NOT NULL COMMENT 'produkt w którym mierzono cenę',
  `direct_offers_count` int(10) unsigned NOT NULL COMMENT 'do obliczeń użyto tylu pasujących (takie samo "co" oraz "zaco")',
  `indirect_offers_count` int(10) unsigned NOT NULL COMMENT 'do obliczeń użyto tylu podobnych (takie samo "co" lub "zaco")',
  PRIMARY KEY (`statID`),
  KEY `resource` (`resource`),
  KEY `server_source_timestamp` (`server_source_timestamp`),
  KEY `prices_measured_in` (`prices_measured_in`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


-- 2016-01-28 00:48:07