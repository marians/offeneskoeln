# encoding: utf-8

"""
Erzeugt Suchindex in Elasticsearch

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
import inspect
import argparse
from datetime import datetime
from pymongo import MongoClient
import pyes
import json
import bson

class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, bson.ObjectId):
            return str(obj)
        elif isinstance(obj, bson.DBRef):
            return {
                'collection': obj.collection,
                '_id': obj.id
            }
        return obj.__dict__


def index_submissions(index):
    """
    Import alle Einträge aus "submissions" in den Index mit dem gegebenen Namen.
    """
    for submission in db.submissions.find({}, {'_id': 1}):
        index_submission(index, submission['_id'])


def index_submission(index, submission_id):
    submission = db.submissions.find_one(submission_id)
    submission['_id'] = str(submission_id)
    # Zugehörige attachments einfügen
    if 'attachments' in submission:
        for n in range(len(submission['attachments'])):
            a = submission['attachments'][n]
            submission['attachments'][n] = db.attachments.find_one(a.id)
            submission['attachments'][n]['_id'] = str(a.id)
            if 'thumbnails' in submission['attachments'][n]:
                del submission['attachments'][n]['thumbnails']
            if 'file' in submission['attachments'][n]:
                del submission['attachments'][n]['file']
            #if any(x in submission['attachments'][n]['name'] for x in cityconfig.SEARCH_IGNORE_ATTACHMENTS):
            #    submission['attachments'][n] = {}
    # Verweisende agendaitems in sessions finden
    committees = []
    sessions = db.sessions.find({'agendaitems.submissions.$id': submission_id}, {'committee_name': 1})
    for session in sessions:
        if 'committee_name' in session:
            committees.append(session['committee_name'])
    if len(committees):
        submission['committees'] = committees
    if 'superordinate' in submission:
        del submission['superordinate']
    if 'subordinate' in submission:
        del submission['subordinate']
    #pprint.pprint(submission)
    print submission
    es.index(submission, index, 'submission', str(submission_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate Fulltext for given City Conf File')
    options = parser.parse_args()
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    host = config.ES_HOST + ':' + str(config.ES_PORT)
    es = pyes.ES(host)

    now = datetime.utcnow()
    new_index = config.ES_INDEX_NAME_PREFIX + '-' + now.strftime('%Y%m%d-%H%M')
    try:
        es.indices.delete_index(new_index)
    except:
        pass

    settings = {
        'index': {
            'analysis': {
                'analyzer': {
                    'my_simple_german_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'standard',
                        'filter': ['standard', 'lowercase', 'my_synonym', 'my_stop']
                    }
                },
                'filter': {
                    'my_synonym': {
                        'type': 'synonym',
                        'synonyms_path': config.SYNONYMS_PATH
                    },
                    'my_stop': {
                        'type': 'stop',
                        'stopwords_path': config.STOPWORDS_PATH
                    }
                }
            }
        }
    }
    print "Creating index %s" % new_index
    es.indices.create_index(new_index, settings=settings)
    # set mapping
    mapping = {
        '_source': {'enabled': False},
        '_all': {'enabled': True},
        'properties': {
            'rs': {
                'store': False,
                'type': 'string'
            },
            'attachments': {
                'store': False,
                'type': 'object'
            },
            'attachments.fulltext': {
                'store': False,
                'type': 'string',
                'index_name': 'attachment_fulltext',
                'index': 'analyzed',
                'analyzer': 'my_simple_german_analyzer'
            },
            'attachments.name': {
                'store': False,
                'type': 'string',
                'index': 'analyzed',
                'analyzer': 'my_simple_german_analyzer'
            },
            'committees': {
                'store': True,
                'type': 'string',
                'index_name': 'committee',
                'index': 'not_analyzed'
            },
            'date': {
                'store': False,
                'type': 'date'
            },
            'georeferences': {
                'store': False,
                'type': 'string',
                'index_name': 'georeference',
                'index': 'analyzed',
                'analyzer': 'my_simple_german_analyzer'
            },
            'georeferences_generated': {
                'store': False,
                'type': 'date'
            },
            'identifier': {
                'store': False,
                'type': 'string',
                'index': 'not_analyzed'
            },
            'last_modified': {
                'store': False,
                'type': 'date'
            },
            'numeric_id': {
                'store': False,
                'type': 'long'
            },
            'original_url': {
                'store': False,
                'type': 'string',
                'index': 'not_analyzed'
            },
            'subject': {
                'store': False,
                'type': 'string',
                'index': 'analyzed',
                'analyzer': 'my_simple_german_analyzer'
            },
            'title': {
                'store': False,
                'type': 'string',
                'index': 'analyzed',
                'analyzer': 'my_simple_german_analyzer'
            },
            'type': {
                'store': True,
                'type': 'string',
                'index': 'not_analyzed'
            }
        }
    }
    es.indices.put_mapping("submission", mapping, [new_index])

    index_submissions(new_index)
    # Setze nach dem Indexieren Alias auf neuen Index
    # z.B. 'offeneskoeln-20130414-1200' -> 'offeneskoeln-latest'
    latest_name = config.ES_INDEX_NAME_PREFIX + '-latest'
    try:
        latest_before = es.get_alias(latest_name)[0]
        print "Aliasing index %s to '%s'" % (new_index, latest_name)
        es.change_aliases([
            ('remove', latest_before, latest_name),
            ('add', new_index, latest_name)
        ])
        print "Deleting index %s" % latest_before
        es.delete_index(latest_before)
    except pyes.exceptions.IndexMissingException:
        es.add_alias(latest_name, [new_index])
