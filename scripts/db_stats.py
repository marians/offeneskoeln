# encoding: utf-8

"""
Datenbank-Statistiken

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
from pymongo import MongoClient


def count_sessions():
    return db.sessions.find({'ags': config.AGS}).count()


def count_submissions():
    return db.submissions.find({'ags': config.AGS}).count()


def count_attachments():
    return db.attachments.find({'ags': config.AGS}).count()


#def count_thumbnails():
#    print db.attachments.aggregate([
#        {"$unwind": "$thumbnails"},
#        {"$group": {"_id": "$thumbnails", "count": {"$sum": 1}}}
#    ])


def count_files():
    return db.fs.files.find().count()


def count_locations():
    return db.locations.find({'ags': config.AGS}).count()


if __name__ == '__main__':
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    print "Number of sessions:    %s" % count_sessions()
    print "Number of submissions: %s" % count_submissions()
    print "Number of attachments: %s" % count_attachments()
    #print "Number of thumbnails:  %s" % count_thumbnails()
    print "Number of files:       %s" % count_files()
    print "Number of locations:   %s" % count_locations()

