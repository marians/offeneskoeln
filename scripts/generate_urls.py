# encoding: utf-8

"""
Finde Straßennamen in Texten und trage Geo-Referenzen
in die entsprechenden Dokumente ein

TODO:
- Straßen aus Datenbank lesen
  https://github.com/marians/offeneskoeln/issues/98

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
import re
import datetime

cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../city")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

def generate_session_urls(db, options):
    if options.new:
        query = {'rs' : cityconfig.RS}
        for doc in db.sessions.find(query):
            delete_url_for_session(doc['_id'], db)
    elif options.reset:
        query = {'rs': cityconfig.RS}
        for doc in db.sessions.find(query):
            generate_url_for_session(doc['_id'], db)
    else:
        # Fehlende Georeferenzen
        query = {'rs': cityconfig.RS, 'url_generated': {'$exists': False}}
        for doc in db.sessions.find(query):
            generate_url_for_session(doc['_id'], db)


def generate_submission_urls(db, options):
    if options.new:
        query = {'rs' : cityconfig.RS}
        for doc in db.submissions.find(query):
            delete_url_for_submission(doc['_id'], db)
    elif options.reset:
        query = {'rs': cityconfig.RS}
        for doc in db.submissions.find(query):
            generate_url_for_submission(doc['_id'], db)
    else:
        # Fehlende Georeferenzen
        query = {'rs': cityconfig.RS, 'url_generated': {'$exists': False}}
        for doc in db.submissions.find(query):
            print doc['id']
            generate_url_for_submission(doc['_id'], db)

def delete_url_for_submission(doc_id, db):
    update = {
        '$unset': {
            'url_generated': 1,
            'urls': 1
        }
    }
    print 'remove %s' % doc_id
    db.submission.update({'_id': doc_id}, update)

def delete_url_for_session(doc_id, db):
    update = {
        '$unset': {
            'url_generated': 1,
            'urls': 1
        }
    }
    print 'remove %s' % doc_id
    db.sessions.update({'_id': doc_id}, update)

def generate_url_for_session(doc_id, db):
    """
    Generiert URLs für Sessions
    """
    session = db.sessions.find_one({'_id': doc_id})
    url = session['identifier']
    url = url.replace('/', '-')
    now = datetime.datetime.utcnow()
    
    # Hier könnte noch viel mehr hin um sprechende URLs zu generieren
    update = {
        '$set': {
            'url_generated': now
        }
    }
    update['$set']['urls'] = [url]
    print ("Writing url %s for submission %s" % (session['identifier'], url))
    db.sessions.update({'_id': doc_id}, update)


def generate_url_for_submission(doc_id, db):
    """
    Generiert URLs für Submissions
    """
    submission = db.submissions.find_one({'_id': doc_id})
    url = submission['identifier']
    url = url.replace('/', '-')
    now = datetime.datetime.utcnow()
    
    # Hier könnte noch viel mehr hin um sprechende URLs zu generieren
    update = {
        '$set': {
            'url_generated': now
        }
    }
    update['$set']['urls'] = [url]
    print ("Writing url %s for submission %s" % (url, submission['identifier']))
    db.submissions.update({'_id': doc_id}, update)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate URLs for given City Conf File')
    parser.add_argument(dest='city', help=("e.g. bochum"))
    parser.add_argument('--new', '-n', action='count', default=0, dest="new",
        help="Regenerates all urls")
    parser.add_argument('--reset', '-r', action='count', default=0, dest="reset",
        help="Resets all urls")
    options = parser.parse_args()
    city = options.city
    cityconfig = __import__(city)
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    generate_session_urls(db, options)
    generate_submission_urls(db, options)
