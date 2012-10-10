CREATE TABLE `attachment_thumbnails` (
  `attachment_id` int(10) unsigned NOT NULL,
  `filename` varchar(32) NOT NULL,
  `width` smallint(5) unsigned NOT NULL,
  `height` smallint(5) unsigned NOT NULL,
  `page` smallint(5) unsigned NOT NULL default '1',
  UNIQUE KEY `filename` (`filename`),
  KEY `attachment_id` (`attachment_id`),
  KEY `page` (`page`),
  KEY `fast` (`attachment_id`,`filename`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `attachment_exclusions` (
  `attachment_id` int(10) unsigned NOT NULL,
  `excluded_since` datetime NOT NULL COMMENT 'Datum, ab welchem das Dokument gesperrt ist (Serverzeit)',
  `reason_code` varchar(30) NOT NULL COMMENT 'Begruendung als maschinenlesbarer Code',
  `reason_text` text COMMENT 'Ausfuehrliche Begruendung, kann HTML z.B. mit Links enthalten',
  PRIMARY KEY  (`attachment_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE `webapp_sessiondata` (
  `session_id` char(128) NOT NULL,
  `atime` timestamp NOT NULL default CURRENT_TIMESTAMP,
  `data` text,
  UNIQUE KEY `session_id` (`session_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
