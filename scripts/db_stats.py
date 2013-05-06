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

import os
import inspect
import argparse
import config
from pymongo import MongoClient

cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../city")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)




def count_sessions():
    return db.sessions.find({'rs': cityconfig.RS}).count()


def count_agendaitems():
    aggregate = db.sessions.aggregate([
        {
            '$project': {
                'agendaitems.id': 1
            }
        },
        {
            '$unwind': "$agendaitems"
        },
        {
            '$group': {
                '_id': "agendaitems",
                'count': {
                    '$sum': 1
                }
            }
        }
    ])
    return aggregate['result'][0]['count']


def count_submissions():
    return db.submissions.find({'rs': cityconfig.RS}).count()


def count_attachments():
    return db.attachments.find({'rs': cityconfig.RS}).count()


def count_depublished_attachments():
    query = {
        'rs': cityconfig.RS,
        'depublication': {'$exists': True}
    }
    return db.attachments.find(query).count()


def count_thumbnails():
    """
    Wir zählen beispielhaft die Thumbnails für eine der Größen
    """
    aggregate = db.attachments.aggregate([
        {
            '$project': {
                'thumbnails.150.filesize': 1
            }
        },
        {
            '$unwind': "$thumbnails.150"
        },
        {
            '$group': {
                '_id': "thumbnails",
                'count': {
                    '$sum': 1
                }
            }
        },
        {
            '$group': {
                '_id': "thumbnails",
                'count': {
                    '$sum': "$count"
                }
            }
        }
    ])
    return aggregate['result'][0]['count']


def thumbnail_size_for_height(height):
    aggregate = db.attachments.aggregate([
        {
            '$project': {
                'thumbnails.' + str(height) + '.filesize': 1
            }
        },
        {
            '$unwind': '$thumbnails.' + str(height)
        },
        {
            '$group': {
                '_id': 'filesize',
                'size': {
                    '$sum': '$thumbnails.' + str(height) + '.filesize'
                }
            }
        }
    ])
    return aggregate['result'][0]['size']


def thumbnails_size():
    tsize = 0
    for height in config.THUMBNAILS_SIZES:
        tsize += thumbnail_size_for_height(height)
    return tsize


def files_size():
    aggregate = db.fs.files.aggregate([
        {
            '$project': {
                'length': 1
            }
        },
        {
            '$group': {
                '_id': 'filesize',
                'value': {
                    '$sum': '$length'
                }
            }
        }
    ])
    return aggregate['result'][0]['value']


def count_files():
    return db.fs.files.find({"rs": cityconfig.RS}).count()


def count_locations():
    return db.locations.find({'rs': cityconfig.RS}).count()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate Fulltext for given City Conf File')
    parser.add_argument(dest='city', help=("e.g. bochum"))
    options = parser.parse_args()
    city = options.city
    cityconfig = __import__(city)
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    print "Number of sessions:                 %s" % count_sessions()
    print "Number of agendaitems:              %s" % count_agendaitems()
    print "Number of submissions:              %s" % count_submissions()
    print "Number of attachments:              %s" % count_attachments()
    print "Number of depublished attachments:  %s" % count_depublished_attachments()
    print "Number of thumbnails:               %s" % count_thumbnails()
    print "File size of thumbnails:            %s" % thumbnails_size()
    print "Number of files in DB:              %s" % count_files()
    print "File size of files in DB:           %s" % files_size()
    print "Number of locations:                %s" % count_locations()
