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
BASE_HOST = 'witten.ris.openruhr.de'

# Regionalschlüssel
RS = "051700024024"

# Name of the location. Use unicode if needed.
#LOCATION_NAME = u'K\xf6ln'
LOCATION_NAME = 'Witten'

#Name der Stadt
CITY_NAME = 'Witten'
#Name der Stadt für Beschreibungen wie "Bochumer Kommunalpolitik"
CITY_NAME_ER = 'Wittener'


# The name of the website. Use unicode!
#APP_NAME = u'Offenes K\xf6ln'
APP_NAME = u'OpenRuhr:RIS:Witten'

APP_TAGLINE = u'Die Lokalpolitik in Witten, einfach zug\xe4nglich'

ICON_URI = '/static/img/logo/favicon_16x16.png'

# Your name
META_PUBLISHER = 'OpenRuhr'
META_DESCR = u'Informationen aus der Lokalpolitik des Ruhrgebietes, zug\xe4nglich dargestellt, durchsuchbar und geografisch zugeordnet.'

# Disqus Comments shortname
DISQUS_SHORTNAME = 'openruhr-ris-witten'
DISQUS_CAT_DOKUMENTE = '2392383'

# Tracking via Piwik oder Google Analytics. Erlaubte Werte: 'PIWIK', 'ANALYTICS' oder leer '' für kein Tracking
TRACKING = 'PIWIK'

# Google Analytics Account
ANALYTICS_ACCOUNT = 'UA-00000000-1'

#PIWIK HOST (kein http:// am Anfang, kein / am Ende)
PIWIK_HOST = 'piwik.sectio-aurea.org'

#PIWIK Site ID
PIWIK_SITE_ID = 38

#Google Site Verification Code, leave empty for deactivate it
GOOGLE_SITE_VERIFICATION = "5cPBydviDSt-NQFMrBn6kXGnuVbYHqVyK3ACsYAYk8g"

# Map view initialization point, should be center of the city
# as Longitude, Latitude tuple
MAP_START_POINT = [7.338387, 51.407961]

#Min und Max Zoom
MAP_TILE_ZOOMLEVEL_MIN = 6
MAP_TILE_ZOOMLEVEL_MAX = 18

# Location settings to be appended to all geocoding requests for street names
GEOCODING_DEFAULT_CITY = 'Witten'
GEOCODING_DEFAULT_COUNTRY = 'DE'
# BBezeichnung irreführend, gemeint ist der Kreis
GEOCODING_FILTER_COUNTY = 'Ennepe-Ruhr-Kreis'

# Suchbeispiele
SEARCH_EXAMPLES = [
    'Grafengalerie', 'Solimare', 'Baustelle', 'Theaterhalle'
]

SEARCH_IGNORE_ATTACHMENTS = [
  'Einladung', 'Niederschrift'
]

#Ursprüngliche URL des Ratsinformationssystems
RIS_ORIGINAL_URL = 'http://buergerinfo.moers.de/'
#URL der Geschäftsordnung
GESCHAEFTSORDNUNG_URL = 'http://www.moers.de/c1257297004f4e94/files/or10-02-geschaeftsordnung.pdf/$file/or10-02-geschaeftsordnung.pdf'

# Monat der Veröffentlichung
PUBLISH_DATE_MONTH = 'Juli 2013'

#Impressum
IMPRESSUM_ORGANISATION = 'Open Knowledge Foundation Deutschland e.V.'
IMPRESSUM_NAME = 'Ernesto Ruge'
IMPRESSUM_STREET = 'Schlesische Str. 6'
IMPRESSUM_CITY = '10997 Berlin'
IMPRESSUM_MAIL = 'info@openruhr.de'
IMPRESSUM_PHONE_URL = '+491731662174'
IMPRESSUM_PHONE_DESCR = '0173 166 21 74'

# Elastic Seaerch Prefix
ES_INDEX_NAME_PREFIX = 'ris-web-moers'

############  Configuration for the API documentation page ###############

# An actually existing submission identifier
API_DOC_EXAMPLE_REFERENCE = 'BBR-SV108/2012'
API_DOC_EXAMPLE_REFERENCE2 = 'A004/2013'
API_DOC_EXAMPLE_COMMITTEE_NAME = 'Bezirksbeirat Rheinau'



### generated vars ####

# Partial path to the static directory
STATIC_URL = BASE_URL + 'static/'

# Partial path to the thumbs directory
THUMBS_URL = BASE_URL + 'static/thumbs/' + RS + '/'

# Attachment URL pattern
ATTACHMENT_DOWNLOAD_URL = BASE_URL + 'anhang/%s.%s'
