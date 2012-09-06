#!/usr/bin/python
# encoding: utf-8

"""
Konfigurationsdatei für die Web-Applikation.

Die Datei wird im github Repository als config_dist.py ausgeliefert. Sie muss in
config.py umbenannt und auf die lokalen Bedingungen angepasst werden.

Mehr unter https://github.com/marians/offeneskoeln/wiki/Leitfaden-für-Entwickler

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

import web

# False ist die richtige Einstellung für die Entwicklung, True für Produktion
cache = False

# Die Basis für alle absoluten URLS
BASE_URL = 'http://localhost:8080/'

# lokaler, absoluter Pfad für den webapp-Ordner
BASE_PATH = '/Users/marian/Documents/Projekte/offeneskoeln.de/webapp'

# URL des Solr-Servers. Für die Entwicklung typischerweise http://localhost:8983/solr
SOLR_URL = 'http://localhost:8983/solr'

# Datenbank-Einstellungen
DB_TYPE = 'mysql'
DB_HOST = 'localhost'
DB_NAME = 'offeneskoeln'
DB_USER = 'offeneskoeln'
DB_PASS = ''

# Name der Webapp Session-Tabelle
HTTP_SESSION_TABLE_NAME = 'webapp_sessiondata'

# Salt-String für die Erzeugung von Session IDs
SESSION_SECRET_KEY = 'xxxxxxxxxxxxxxxxx'

# Schlüssel der Yahoo! Placefinder App
# Besorg Dir zum Entwickeln einen eigenen unter
# http://developer.yahoo.com/geo/placefinder/
PLACEFINDER_APP_ID = 'xxxxxxxx'

# Name der Stadt, der bei allen Placefinder-Anfragen übergeben wird
PLACEFINDER_DEFAULT_CITY = 'Cologne'

# Land, das bei allen Placefinder-Anfragen übergeben wird
PLACEFINDER_DEFAULT_COUNTRY = 'DE'

# Debugging aktivieren/deaktivieren
# Empfehlung: False - Auf der Konsole gibt es immer noch reichlich Output.
web.config.debug = False

web.config.db_parameters = {
    'dbn': DB_TYPE,
    'host': DB_HOST,
    'user': DB_USER,
    'pw': DB_PASS,
    'db': DB_NAME
}
web.config.session_parameters = {
    'cookie_name': 'okde',
    'cookie_domain': None,
    'cookie_path': '/',
    'timeout': 60 * 60 * 24,
    'secret_key': SESSION_SECRET_KEY,
    'ignore_change_ip': True,
    'ignore_expiry': True,
    'httponly': True,
    'secure': False
}
web.config.handler_parameters = {
    'db_table': HTTP_SESSION_TABLE_NAME
}

DB = web.database(dbn=DB_TYPE, db=DB_NAME, user=DB_USER, pw=DB_PASS)

# Ratsinfomrationssystem Köln URLs
#
# URL-Muster für Anträge
RIS_AG_URLPATTERN = 'http://ratsinformation.stadt-koeln.de/ag0050.asp?__kagnr=%d'
# URL-Muster für Vorlagen
RIS_VO_URLPATTERN = 'http://ratsinformation.stadt-koeln.de/vo0050.asp?__kvonr=%d'

