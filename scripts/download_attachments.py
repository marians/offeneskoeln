#!/usr/bin/env python
# encoding: utf-8

"""
Lädt Anhänge eines bestimmten Datumsbereichs herunter

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

import sys
sys.path.append('./')
import config
import os
import json
import urllib
from optparse import OptionParser


def get_documents(date=None):
    """
    Führt den API-Request für das Abrufen von Dokumenten aus
    """
    url = 'http://offeneskoeln.de/api/documents'
    url += '?docs=10000&output=attachments&date=%s' % date
    request = urllib.urlopen(url)
    if request.getcode() != 200:
        sys.stderr.write('Bad HTTP Status: ' + str(request.getcode()))
        sys.stderr.write(request.read())
    else:
        jsons = request.read()
        return json.loads(jsons)

if __name__ == '__main__':
    usage = "usage: %prog <daterange>"
    usage += "\n\nWhere daterange is e.g. 2010-2011 or 201208-201209"
    parser = OptionParser(usage=usage)
    parser.add_option("-f", "--folder", dest="folder",
                  help="write files to folder FOLDER", metavar="FOLDER")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("No date range given")
    if options.folder is None:
        options.folder = '.'
    result = get_documents(args[0])
    num = result['response']['numhits']
    print num, "Document(s) found"
    if num > 0:
        for doc in result['response']['documents']:
            if 'attachments' in doc:
                for attachment in doc['attachments']:
                    print "Downloading", attachment['url']
                    filename = attachment['url'].split('/')[-1]
                    path = options.folder + os.sep + filename
                    urllib.urlretrieve(attachment['url'], filename)
