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
BASE_URL = 'http://infinite-ris/'

# Basis Host
BASE_HOST = 'bochum.ris.openruhr.de'

# Regionalschlüssel
RS = "059110000000"

# Name of the location. Use unicode if needed.
#LOCATION_NAME = u'K\xf6ln'
LOCATION_NAME = 'Bochum'

#Name der Stadt
CITY_NAME = 'Bochum'
#Name der Stadt für Beschreibungen wie "Bochumer Kommunalpolitik"
CITY_NAME_ER = 'Bochumer'


# The name of the website. Use unicode!
#APP_NAME = u'Offenes K\xf6ln'
APP_NAME = u'OpenRuhr:RIS:Bochum'

APP_TAGLINE = u'Die Lokalpolitik in Bochum, einfach zug\xe4nglich'

ICON_URI = '/static/img/logo/favicon_16x16.png'

# Your name
META_PUBLISHER = 'OpenRuhr'
META_DESCR = u'Informationen aus der Lokalpolitik des Ruhrgebietes, zug\xe4nglich dargestellt, durchsuchbar und geografisch zugeordnet.'

# Disqus Comments shortname
DISQUS_SHORTNAME = 'openruhr-ris-bochum'
DISQUS_CAT_DOKUMENTE = '2392348'

# Tracking via Piwik oder Google Analytics. Erlaubte Werte: 'PIWIK', 'ANALYTICS' oder leer '' für kein Tracking
TRACKING = 'PIWIK'

# Google Analytics Account
ANALYTICS_ACCOUNT = 'UA-00000000-1'

#PIWIK HOST (kein http:// am Anfang, kein / am Ende)
PIWIK_HOST = 'piwik.sectio-aurea.org'

#PIWIK Site ID
PIWIK_SITE_ID = 34

#Google Site Verification Code, leave empty for deactivate it
GOOGLE_SITE_VERIFICATION = "5cPBydviDSt-NQFMrBn6kXGnuVbYHqVyK3ACsYAYk8g"

# Map view initialization point, should be center of the city
# as Longitude, Latitude tuple
MAP_START_POINT = [7.216236, 51.481845,]

#Min und Max Zoom
MAP_TILE_ZOOMLEVEL_MIN = 4
MAP_TILE_ZOOMLEVEL_MAX = 18

# Location settings to be appended to all geocoding requests for street names
GEOCODING_DEFAULT_CITY = 'Bochum'
GEOCODING_DEFAULT_COUNTRY = 'DE'
GEOCODING_FILTER_COUNTY = 'Bochum'

# Suchbeispiele
SEARCH_EXAMPLES = [
  'Musikzentrum', 'Rathaus', 'Bergbaumuseum', 'Opel'
]

SEARCH_IGNORE_ATTACHMENTS = [
  'Einladung', 'Niederschrift'
]

#Ursprüngliche URL des Ratsinformationssystems
RIS_ORIGINAL_URL = 'https://session.bochum.de/'
#URL der Geschäftsordnung
GESCHAEFTSORDNUNG_URL = 'http://www.bochum.de/C12571A3001D56CE/vwContentByKey/N26R26TB834HGILDE/$file/rat_geschaeftsordnung.pdf'

# Monat der Veröffentlichung
PUBLISH_DATE_MONTH = 'Mai 2013'

#Impressum
IMPRESSUM_NAME = 'Ernesto Ruge'
IMPRESSUM_STREET = u'Zechenstra\xdfe 27'
IMPRESSUM_CITY = '44791 Bochum'
IMPRESSUM_MAIL = 'mail@ernestoruge.de'
IMPRESSUM_PHONE_URL = '+491731662174'
IMPRESSUM_PHONE_DESCR = '0173 166 21 74'


# Elastic Seaerch Prefix
ES_INDEX_NAME_PREFIX = 'ris-web-bochum'

############  Configuration for the API documentation page ###############

# An actually existing submission identifier
API_DOC_EXAMPLE_REFERENCE = 'BBR-SV108/2012'
API_DOC_EXAMPLE_REFERENCE2 = 'A004/2013'
API_DOC_EXAMPLE_COMMITTEE_NAME = 'Bezirksbeirat Rheinau'

### generated vars ####

# Partial path to the static directory
STATIC_URL = BASE_URL + 'static/'

# Partial path to the thumbs directory
THUMBS_URL = BASE_URL + 'static/thumbs/'

# Attachment URL pattern
ATTACHMENT_DOWNLOAD_URL = BASE_URL + 'anhang/%s.%s'
