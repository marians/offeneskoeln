# encoding: utf-8

"""
Erzeugt Volltexte zu allen Attachments in der Datenbank

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
import config
import tempfile
import subprocess
from pymongo import MongoClient
import gridfs
import datetime
import time
import argparse
from bson import ObjectId, DBRef
import types

STATS = {
  'attachments_without_fulltext': 0,
  'attachments_with_outdated_fulltext': 0,
  'fulltext_created': 0,
  'fulltext_not_created': 0
}

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

def generate_fulltext(db, config, body_id):
  """Generiert Volltexte für die gesamte file-Collection"""

  # Files mit veralteten Volltexten
  query = {'fulltextGenerated': {'$exists': True}, 'depublication': {'$exists': False}, 'body': DBRef('body', ObjectId(body_id))}
  for single_file in db.file.find(query):
    # Dateiinfo abholen
    file_data = db.fs.files.find_one({'_id': single_file['file'].id})
    if file_data['uploadDate'] > single_file['fulltextGenerated']:
      # Volltext muss erneuert werden
      STATS['attachments_with_outdated_fulltext'] += 1
      generate_fulltext_for_file(db, config,file_data['_id'])

  # Files ohne Volltext
  query = {'fulltextGenerated': {'$exists': False}, 'body': DBRef('body', ObjectId(body_id))}
  for single_file in db.file.find(query):
    STATS['attachments_without_fulltext'] += 1
    generate_fulltext_for_file(db, config, single_file['_id'])


def store_tempfile(file_id, db):
  file = db.file.find_one({'_id': file_id}, {'file': 1, 'filename': 1})
  file_data = fs.get(file['file'].id)
  temppath = tempdir + os.sep + file_data.filename
  tempf = open(temppath, 'wb')
  tempf.write(file_data.read())
  tempf.close()
  return temppath


def generate_fulltext_for_file(db, config, file_id):
  """
  Generiert alle Thumbnails fuer ein bestimmtes Attachment
  """
  # temporaere Datei des Attachments anlegen
  print "Processing file_id=%s" % (file_id)
  path = store_tempfile(file_id, db)

  cmd = config['pdf_to_text_cmd'] + ' -nopgbrk -enc UTF-8 ' + path + ' -'
  text = execute(cmd)
  if text is not None:
    text = text.strip()
    text = text.decode('utf-8')
    text = text.replace(u"\u00a0", " ")

  # delete temp file
  os.unlink(path)
  now = datetime.datetime.utcnow()
  update = {
    '$set': {
      'fulltextGenerated': now,
      'lastModified': now
    }
  }
  if text is None or text == '':
    STATS['fulltext_not_created'] += 1
  else:
    update['$set']['fulltext'] = text
    STATS['fulltext_created'] += 1
  db.file.update({'_id': file_id}, update)


def execute(cmd):
  output, error = subprocess.Popen(
    cmd.split(' '), stdout=subprocess.PIPE,
    stderr=subprocess.PIPE).communicate()
  if error is not None and error.strip() != '':
    print >> sys.stderr, "Command: " + cmd
    print >> sys.stderr, "Error: " + error
  return output


def milliseconds():
  """Return current time as milliseconds int"""
  return int(round(time.time() * 1000))


def print_stats():
  for key in STATS.keys():
    print "%s: %d" % (key, STATS[key])

if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    description='Generate Fulltext for given Body ID')
  parser.add_argument(dest='body_id', help=("e.g. 54626a479bcda406fb531236"))
  options = parser.parse_args()
  body_id = options.body_id
  connection = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
  db = connection[config.MONGO_DBNAME]
  fs = gridfs.GridFS(db)
  config = get_config(db, body_id)
  tempdir = tempfile.mkdtemp()
  generate_fulltext(db, config, body_id)
  os.rmdir(tempdir)
  print_stats()
