# encoding: utf-8

"""
Stadt-Konfiguration für die Webapp und Kommandozeilen-Scripte

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

import locale

# The basis for all absolute URLs on this site
BASE_URL = 'http://localhost:5000/'

BASE_HOST = 'bochum.ris.openruhr.de'


# Regionalschlüssel
RS = "082220000000"  # Mannheim

ES_INDEX_NAME_PREFIX = 'offeneskoeln'

# Your name
META_PUBLISHER = 'Manfred Mustermann'
META_DESCR = 'Informationen aus der Lokalpolitik des Ruhrgebietes, zugänglich dargestellt, durchsuchbar und geografisch zugeordnet.'


# Map view initialization point, should be center of the city
# as Longitude, Latitude tuple
MAP_START_POINT = [8.4666, 49.48734]

# The name of the website. Use unicode!
#APP_NAME = u'Offenes K\xf6ln'
APP_NAME = u'OpenRuhr:Bochum'

#Name der Stadt
CITY_NAME = 'Bochum'
#Name der Stadt für Beschreibungen wie "Bochumer Kommunalpolitik"
CITY_NAME_ER = 'Bochumer'

ICON_URI = '/static/img/logo/favicon_16x16.png'

APP_TAGLINE = u'Die Lokalpolitik in Mannheim, einfach zug\xe4nglich'

SEARCH_EXAMPLES = [
  'Bundesgartenschau', 'Planken', 'Ludwigshafen', 'Quadrate'
]

# Location settings to be appended to all geocoding requests for street names
GEOCODING_DEFAULT_CITY = 'Mannheim'
GEOCODING_DEFAULT_COUNTRY = 'DE'
GEOCODING_FILTER_COUNTY = 'Mannheim'

#Ursprüngliche URL des Ratsinformationssystems
RIS_ORIGINAL_URL = 'https://session.bochum.de/'
#URL der Geschäftsordnung
GESCHAEFTSORDNUNG_URL = ''


# Tracking via Piwik oder Google Analytics. Erlaubte Werte: 'PIWIK', 'ANALYTICS' oder leer '' für kein Tracking
TRACKING = ''

# Google Analytics Account
ANALYTICS_ACCOUNT = 'UA-00000000-1'

#PIWIK HOST (kein http:// am Anfang, kein / am Ende)
PIWIK_HOST = 'piwik.sectio-aurea.org'

#PIWIK Site ID
PIWIK_SITE_ID = 10

PUBLISH_DATE_MONTH = 'Mai 2013'

IMPRESSUM_NAME = ''
IMPRESSUM_STREET = ''
IMPRESSUM_CITY = ''
IMPRESSUM_MAIL = ''
IMPRESSUM_PHONE_URL = ''
IMPRESSUM_PHONE_DESCR = ''

############  Configuration for the API documentation page ###############

# An actually existing submission identifier
API_DOC_EXAMPLE_REFERENCE = 'BBR-SV108/2012'
API_DOC_EXAMPLE_REFERENCE2 = 'A004/2013'
API_DOC_EXAMPLE_COMMITTEE_NAME = 'Bezirksbeirat Rheinau'
