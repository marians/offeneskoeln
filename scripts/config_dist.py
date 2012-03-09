#!/usr/bin/env python
# encoding: utf-8

"""
Konfiguration für Python-basierte Scripte

Die Einstellungen in dieser Datei müssen der jeweiligen Umgebung angepasst
und der Name der Datei zu "config.py" geändert werden.

Copyright (c) 2012 Marian Steinbach

Hiermit wird unentgeltlich jeder Person, die eine Kopie der Software und
der zugehörigen Dokumentationen (die "Software") erhält, die Erlaubnis
erteilt, sie uneingeschränkt zu benutzen, inklusive und ohne Ausnahme, dem
Recht, sie zu verwenden, kopieren, ändern, fusionieren, verlegen,
verbreiten, unterlizenzieren und/oder zu verkaufen, und Personen, die diese
Software erhalten, diese Rechte zu geben, unter den folgenden Bedingungen:

Der obige Urheberrechtsvermerk und dieser Erlaubnisvermerk sind in allen
Kopien oder Teilkopien der Software beizulegen.

Die Software wird ohne jede ausdrückliche oder implizierte Garantie
bereitgestellt, einschließlich der Garantie zur Benutzung für den
vorgesehenen oder einen bestimmten Zweck sowie jeglicher Rechtsverletzung,
jedoch nicht darauf beschränkt. In keinem Fall sind die Autoren oder
Copyrightinhaber für jeglichen Schaden oder sonstige Ansprüche haftbar zu
machen, ob infolge der Erfüllung eines Vertrages, eines Delikts oder anders
im Zusammenhang mit der Software oder sonstiger Verwendung der Software
entstanden.
"""

# Basis-URL für Solr Webservice
SOLR_URL = 'http://127.0.0.1:8983/solr'

# Root-Verzeichnis der Webapp
WWW_PATH = '/var/www/offeneskoeln.de'

# Pfad des Attachments-Verzeichnisses
ATTACHMENTS_PATH = WWW_PATH + '/attachments'

# Pfad für statische Dateien unterhalb der Webapp
STATIC_PATH = WWW_PATH + '/static'

# Pfad für Thumbnails (typischerweise unterhalb von STATIC_PATH)
THUMBS_PATH = STATIC_PATH + '/thumbs'

# Datenbank-Konfiguration
DB_HOST = 'localhost'
DB_USER = 'offeneskoeln'
DB_PASS = ''
DB_NAME = 'offeneskoeln'

# Tabelle für Thumbnail-Informationen
DB_THUMBS_TABLE = 'attachment_thumbnails'

# Straßenverzeichnis (Liste aller bekannten Straßennamen)
STREETS_FILE = '../data/strassen.txt'
