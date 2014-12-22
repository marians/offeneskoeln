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
import config
import types
from bson import ObjectId, DBRef

def get_config(db, body_id):
  """
  Returns Config JSON
  """
  config = db.config.find_one()
  if '_id' in config:
    del config['_id']
  local_config = db.body.find_one({'_id': ObjectId(body_id)})
  if 'config' in local_config:
    config = merge_dict(config, local_config['config'])
    del local_config['config']
  config['city'] = local_config
  return config

def merge_dict(x, y):
  merged = dict(x,**y)
  xkeys = x.keys()
  for key in xkeys:
    if type(x[key]) is types.DictType and y.has_key(key):
      merged[key] = merge_dict(x[key],y[key])
  return merged


def generate_georeferences(config, db, options):
  """Generiert Geo-Referenzen für die gesamte paper-Collection"""

  if options.new:
    query = {'body' : DBRef('body', (ObjectId(options.body_id)))}
    for paper in db.paper.find(query):
      delete_georeferences_for_paper(paper['_id'], db)
  elif options.reset:
    query = {'body' : DBRef('body', (ObjectId(options.body_id)))}
    for paper in db.paper.find(query):
      generate_georeferences_for_paper(config, paper['_id'], db)
  else:
    # Georeferenzen die ein Update benötigen
    query = {'body' : DBRef('body', (ObjectId(options.body_id))), 'georeferencesGenerated': {'$exists': True}}
    for paper in db.paper.find(query):
      to_update = False
      # Datumsabgleich der letzten Modifizierung der Session
      if paper['lastModified'] > paper['georeferencesGenerated']:
        to_update = True
      # Datumsabgleich der generierten Fulltexts
      if 'mainFile' in paper:
        paper['mainFile'] = db.dereference(paper['mainFile'])
        if 'fulltextGenerated' in paper['mainFile']:
          if paper['mainFile']['fulltextGenerated'] > paper['georeferencesGenerated']:
            to_update = True
      if 'invitation' in paper:
        paper['invitation'] = db.dereference(paper['invitation'])
        if 'fulltextGenerated' in paper['invitation']:
          if paper['invitation']['fulltextGenerated'] > paper['georeferencesGenerated']:
            to_update = True
      if 'auxiliaryFile' in paper:
        for i in range(len(paper['auxiliaryFile'])):
          paper['auxiliaryFile'][i] = db.dereference(paper['auxiliaryFile'][i])
          if 'fulltextGenerated' in paper['auxiliaryFile'][i]:
            if paper['auxiliaryFile'][i]['fulltextGenerated'] > paper['georeferencesGenerated']:
              to_update = True
      
      if to_update:
        generate_georeferences_for_paper(config, paper['_id'], db)
    # Fehlende Georeferenzen
    query = {'body' : DBRef('body', (ObjectId(options.body_id))), 'georeferencesGenerated': {'$exists': False}}
    for paper in db.paper.find(query):
      generate_georeferences_for_paper(config, paper['_id'], db)



def delete_georeferences_for_paper(paper_id, db):
  update = {
    '$unset': {
      'georeferencesGenerated': 1,
      'georeferences': 1
    }
  }
  print 'remove %s' % paper_id
  db.paper.update({'_id': paper_id}, update)



def generate_georeferences_for_paper(config, paper_id, db):
  """
  Lädt die Texte zu einer Submission, gleicht darin
  Straßennamen ab und schreibt das Ergebnis in das
  Submission-Dokument in der Datenbank.
  """
  paper = db.paper.find_one({'_id': paper_id})
  if 'name' in paper:
    name = paper['name']
  text = ''
  if 'mainFile' in paper:
    text += " " + get_file_fulltext(config, paper['mainFile'].id)
  if 'invitation' in paper:
    text += " " + get_file_fulltext(config, paper['invitation'].id)

  if 'auxiliaryFile' in paper:
    for i in range(len(paper['auxiliaryFile'])):
      text += " " + get_file_fulltext(config, paper['auxiliaryFile'][i].id)
  result = match_streets(text)
  now = datetime.datetime.utcnow()
  update = {
    '$set': {
      'georeferencesGenerated': now
    }
  }
  update['$set']['georeferences'] = result
  print ("Writing %d georeferences to paper %s" %
    (len(result), paper_id))
  db.paper.update({'_id': paper_id}, update)


def get_file_fulltext(config, file_id):
  """
  Gibt den Volltext zu einem file aus
  """
  file = db.file.find_one({'_id': ObjectId(file_id)})
  if 'fulltext' in file:
    if 'name' in file:
      if any(x in file['name'] for x in config['search_ignore_files']):
        return ''
    return file['fulltext']
  return ''


def load_streets(config, options, db):
  """
  Lädt eine Straßenliste (ein Eintrag je Zeile UTF-8)
  in ein Dict. Dabei werden verschiedene Synonyme für
  Namen, die auf "straße" oder "platz" enden, angelegt.
  """
  nameslist = []
  query = {"body" : DBRef('body', ObjectId(options.body_id)) }
  for street in db.locations.find(query):
    nameslist.append(street['name'])
  ret = {}
  pattern1 = re.compile(".*straße$")
  pattern2 = re.compile(".*Straße$")
  pattern3 = re.compile(".*platz$")
  pattern4 = re.compile(".*Platz$")
  for name in nameslist:
    ret[name.replace(' ', '-')] = name
    # Alternative Schreibweisen: z.B. straße => str.
    alternatives = []
    if pattern1.match(name):
      alternatives.append(name.replace('straße', 'str.'))
      alternatives.append(name.replace('straße', 'str'))
      alternatives.append(name.replace('straße', ' Straße'))
      alternatives.append(name.replace('straße', ' Str.'))
      alternatives.append(name.replace('straße', ' Str'))
    elif pattern2.match(name):
      alternatives.append(name.replace('Straße', 'Str.'))
      alternatives.append(name.replace('Straße', 'Str'))
      alternatives.append(name.replace(' Straße', 'straße'))
      alternatives.append(name.replace(' Straße', 'str.'))
      alternatives.append(name.replace(' Straße', 'str'))
    elif pattern3.match(name):
      alternatives.append(name.replace('platz', 'pl.'))
      alternatives.append(name.replace('platz', 'pl'))
    elif pattern4.match(name):
      alternatives.append(name.replace('Platz', 'Pl.'))
      alternatives.append(name.replace('Platz', 'Pl'))
    for alt in alternatives:
      ret[alt.replace(' ', '-')] = name
  return ret


def match_streets(text):
  """
  Findet alle Vorkommnisse einer Liste von Straßennamen
  in dem gegebenen String und gibt sie
  als Liste zurück
  """
  results = {}
  for variation in streets.keys():
    if variation in text:
      results[streets[variation]] = True
  return sorted(results.keys())


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    description='Generate Fulltext for given Body ID')
  parser.add_argument(dest='body_id', help=("e.g. 54626a479bcda406fb531236"))
  parser.add_argument('--new', '-n', action='count', default=0, dest="new",
    help="Regenerates all georeferences")
  parser.add_argument('--reset', '-r', action='count', default=0, dest="reset",
    help="Resets all georeferences")
  options = parser.parse_args()
  body_id = options.body_id
  connection = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
  db = connection[config.MONGO_DBNAME]
  config = get_config(db, body_id)
  streets = load_streets(config, options, db)
  generate_georeferences(config, db, options)
