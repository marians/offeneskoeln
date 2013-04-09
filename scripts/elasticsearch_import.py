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

import config
import os
import sys
from datetime import datetime
from pymongo import MongoClient
import pyes
import pprint
import json


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
    if 'superordinate' in submission:
        del submission['superordinate']
    if 'subordinate' in submission:
        del submission['subordinate']
    #pprint.pprint(submission)
    es.index(submission, index, 'submission', str(submission_id))


if __name__ == '__main__':
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    es = pyes.ES('localhost:9200')

    now = datetime.utcnow()
    #new_index = config.ES_INDEX + '-' + now.strptime('%Y%m%d-%H%M')
    new_index = 'offeneskoeln' + '-' + now.strftime('%Y%m%d-%H%M')
    try:
        es.indices.delete_index(new_index)
    except:
        pass
    es.indices.create_index(new_index)

    # set mapping
    mapping = {
        '_source': {'enabled': False},
        '_all': {'enabled': True},
        'properties': {
            'ags': {
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
                'indexed': 'analyzed'
            },
            'attachments.name': {
                'store': False,
                'type': 'string',
                'indexed': 'analyzed'
            },
            'date': {
                'store': False,
                'type': 'date'
            },
            'georeferences': {
                'store': False,
                'type': 'string',
                'index_name': 'georeference',
                'indexed': 'analyzed'
            },
            'georeferences_generated': {
                'store': False,
                'type': 'date'
            },
            'identifier': {
                'store': False,
                'type': 'string',
                'indexed': 'not_analyzed'
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
                'indexed': 'not_analyzed'
            },
            'subject': {
                'store': False,
                'type': 'string',
                'indexed': 'analyzed'
            },
            'title': {
                'store': False,
                'type': 'string',
                'indexed': 'analyzed'
            },
            'type': {
                'store': False,
                'type': 'string',
                'indexed': 'not_analyzed'
            }
        }
    }
    es.indices.put_mapping("submission", mapping, [new_index])

    index_submissions(new_index)
    # Setze nach dem Indexieren Alias auf neuen Index
    # z.B. 'offeneskoeln-20130414-1200' -> 'offeneskoeln-latest'
    #latest_name = config.ES_INDEX + '-latest'
    latest_name = 'offeneskoeln' + '-latest'
    try:
        latest_before = es.get_alias(latest_name)
        es.change_aliases([
            ('remove', latest_before, latest_name),
            ('add', new_index, latest_name)
        ])
    except pyes.exceptions.IndexMissingException:
        es.add_alias(latest_name, [new_index])
