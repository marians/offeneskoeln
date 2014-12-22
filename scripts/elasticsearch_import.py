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

import config as sysconfig
import os
import inspect
import argparse
from datetime import datetime
from pymongo import MongoClient
import pyes
import json
from bson import ObjectId, DBRef


def get_config(db):
  """
  Returns Config JSON
  """
  config = db.config.find_one()
  if '_id' in config:
    del config['_id']
  return config

def merge_dict(x, y):
  merged = dict(x,**y)
  xkeys = x.keys()
  for key in xkeys:
    if type(x[key]) is types.DictType and y.has_key(key):
      merged[key] = merge_dict(x[key],y[key])
  return merged

class MyEncoder(json.JSONEncoder):
  def default(self, obj):
    if isinstance(obj, datetime.datetime):
      return obj.isoformat()
    elif isinstance(obj, ObjectId):
      return str(obj)
    elif isinstance(obj, DBRef):
      return {
        'collection': obj.collection,
        '_id': obj.id
      }
    return obj.__dict__



def index_papers(config, index):
  """
  Import alle Einträge aus paper in den Index mit dem gegebenen Namen.
  """
  for paper in db.paper.find({}, {'_id': 1}):
    index_paper(config, index, paper['_id'])


def index_paper(config, index, paper_id):
  paper = db.paper.find_one(paper_id)
  # Body dereferenzieren
  paper['body'] = db.dereference(paper['body'])
  # Zugehörige files sammeln
  files = []
  if 'mainFile' in paper:
    files.append(db.dereference(paper['mainFile']))
  if 'auxiliaryFile' in paper:
    for n in range(len(paper['auxiliaryFile'])):
      files.append(db.dereference(paper['auxiliaryFile'][n]))
  if 'invitation' in paper:
    files.append(db.dereference(paper['invitation']))
  # Ergebnis-Dict erstellen
  result = {
    '_id': str(paper['_id']),
    'file': [],
    'bodyId': str(paper['body']['_id']),
    'bodyName': paper['body']['name']
  }
  if 'publishedDate' in paper:
    result['publishedDate'] = paper['publishedDate']
  if 'originalId' in paper:
    result['originalId'] = paper['originalId']
  if 'reference' in paper:
    result['reference'] = paper['reference']
  if 'name' in paper:
    result['name'] = paper['name']
  if 'paperType' in paper:
    result['paperType'] = paper['paperType']
  for file in files:
    result_file = {
      'id': str(file['_id'])
    }
    if 'fulltext' in file:
      result_file['fulltext'] = file['fulltext']
    if 'name' in file:
      result_file['name'] = file['name']
    result['file'].append(result_file)
  es.index(result, index, 'paper', str(paper_id))


"""
def index_submissions(index):
  """
#Import alle Einträge aus "submissions" in den Index mit dem gegebenen Namen.
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
      #  submission['attachments'][n] = {}
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
  print submission
  es.index(submission, index, 'submission', str(submission_id))
"""

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    description='Generate Fulltext for given City Conf File')
  options = parser.parse_args()
  connection = MongoClient(sysconfig.MONGO_HOST, sysconfig.MONGO_PORT)
  db = connection[sysconfig.MONGO_DBNAME]
  config = get_config(db)
  host = sysconfig.ES_HOST + ':' + str(sysconfig.ES_PORT)
  es = pyes.ES(host)

  now = datetime.utcnow()
  new_index = config['es_paper_index'] + '-' + now.strftime('%Y%m%d-%H%M')
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
            'synonyms_path': config['synonyms_path']
          },
          'my_stop': {
            'type': 'stop',
            'stopwords_path': config['stopwords_path']
          }
        }
      }
    }
  }
  print "Creating index %s" % new_index
  es.indices.create_index(new_index, settings=settings)
  # set mapping
  mapping = {
    '_source': {'enabled': True},
    '_all': {'enabled': True},
    'properties': {
      'bodyId': {
        'store': True,
        'type': 'string',
        'index': 'not_analyzed'
      },
      'bodyName': {
        'store': True,
        'type': 'string',
        'index': 'not_analyzed'
      },
      'file': {
        'store': False,
        'type': 'object'
      },
      'file.id': {
        'store': True,
        'type': 'string',
        'index': 'analyzed'
      },
      'file.name': {
        'store': True,
        'type': 'string',
        'index_name': 'fileName',
        'index': 'analyzed',
        'analyzer': 'my_simple_german_analyzer'
      },
      'file.fulltext': {
        'store': True,
        'type': 'string',
        'index_name': 'fileFulltext',
        'index': 'analyzed',
        'analyzer': 'my_simple_german_analyzer'
      },
      #'organization': {
      #  'store': True,
      #  'type': 'string',
      #  'index_name': 'committee',
      #  'index': 'not_analyzed'
      #},
      #'georeferences': {
      #  'store': False,
      #  'type': 'string',
      #  'index_name': 'georeference',
      #  'index': 'analyzed',
      #  'analyzer': 'my_simple_german_analyzer'
      #},
      #'georeferencesGenerated': {
      #  'store': False,
      #  'type': 'date'
      #},
      'publishedDate': {
        'store': True,
        'type': 'date'
      },
      'originalId': {
        'store': False,
        'type': 'string',
        'index': 'not_analyzed'
      },
      'originalUrl': {
        'store': False,
        'type': 'string',
        'index': 'not_analyzed'
      },
      'reference': {
        'store': False,
        'type': 'string',
        'index': 'not_analyzed'
      },
      'name': {
        'store': True,
        'type': 'string',
        'index': 'analyzed',
        'analyzer': 'my_simple_german_analyzer'
      },
      'paperType': {
        'store': True,
        'type': 'string',
        'index': 'not_analyzed'
      }
    }
  }
  es.indices.put_mapping("paper", mapping, [new_index])

  index_papers(config, new_index)
  # Setze nach dem Indexieren Alias auf neuen Index
  # z.B. 'paper-20130414-1200' -> 'paper-latest'
  latest_name = config['es_paper_index'] + '-latest'
  try:
    latest_before = es.indices.get_alias(latest_name)[0]
    print "Aliasing index %s to '%s'" % (new_index, latest_name)
    es.indices.change_aliases([
      ('remove', latest_before, latest_name, {}),
      ('add', new_index, latest_name, {})
    ])
    print "Deleting index %s" % latest_before
    es.indices.delete_index(latest_before)
  except pyes.exceptions.IndexMissingException:
    print "Aliasing index %s to '%s'" % (new_index, latest_name)
    es.indices.add_alias(latest_name, [new_index])
