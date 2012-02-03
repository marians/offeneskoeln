CREATE TABLE IF NOT EXISTS `geo_nodes` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `latitude` decimal(10,7) default NULL,
  `longitude` decimal(10,7) default NULL,
  PRIMARY KEY  (`id`),
  KEY `latitudelongitude` (`latitude`,`longitude`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `geo_objects` (
  `id` int(11) unsigned NOT NULL auto_increment,
  `name` varchar(255) default NULL,
  `type` varchar(100) default NULL,
  `subtype` varchar(100) default NULL,
  PRIMARY KEY  (`id`),
  KEY `nameindex` (`name`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `geo_objects2nodes` (
  `object_id` int(11) unsigned NOT NULL,
  `node_id` int(11) unsigned NOT NULL,
  UNIQUE KEY `quickfind` (`object_id`,`node_id`),
  KEY `object_id` (`object_id`),
  KEY `node_id` (`node_id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
