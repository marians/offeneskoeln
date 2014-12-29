# encoding: utf-8

"""
Erstellt ein tar.bz2 Paket der Anhänge eines bestimmten Datumsbereichs.
Dabei wird das Änderungsdatum der Datei berücksichtigt - also der
Zeitpunkt, zu dem die Datei abgerufen wurde.

Copyright (c) 2012 Marian Steinbach, Ernesto Ruge

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
os.environ['CITY_CONF']='/opt/ris-web/city/template.py'

import config
import inspect
import argparse
import datetime
from webapp import date_range
from pymongo import MongoClient
import gridfs
import subprocess
import config
from bson import DBRef, ObjectId


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

def save_file(fs, file_id, path):
  """
  Copy a file from MongoDB GridFS to a local file system path
  """
  file_data = fs.get(file_id)
  tempf = open(path, 'wb')
  tempf.write(file_data.read())
  tempf.close()
  return path

def create_download_package(extconfig, db, fs, body_id):
  """
  daterange: a datetime tuple compatible string
  folder: The target folder and final output filename prefix
  """
  execute('rm -f %s.tar.bz2' % extconfig['files_dump_folder'] + os.sep + body_id + os.sep)
  
  tmp_folder = (extconfig['files_dump_folder'] + os.sep + body_id + os.sep)
  if not os.path.exists(tmp_folder):
    os.makedirs(tmp_folder)
  
  for file in db.fs.files.find({'body': DBRef('body', ObjectId(body_id))}):
    file_id = file['_id']
    path = tmp_folder + str(file_id) + '_' + file['filename']
    save_file(fs, file_id, path)
  execute('tar -cjf %s.tar.bz2 -C %s .' % (extconfig['files_dump_folder'] + os.sep + body_id, tmp_folder))
  execute('rm -rf %s' % tmp_folder)


def execute(cmd):
  output, error = subprocess.Popen(
    cmd.split(' '), stdout=subprocess.PIPE,
    stderr=subprocess.PIPE).communicate()
  if error is not None and error.strip() != '':
    print >> sys.stderr, "Command: " + cmd
    print >> sys.stderr, "Error: " + error


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Generate a database dump')
  parser.add_argument('-b', dest='body_id', default=None)
  options = parser.parse_args()
  body_id = options.body_id
  
  connection = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
  db = connection[config.MONGO_DBNAME]
  fs = gridfs.GridFS(db)
  extconfig = get_config(db)
  
  if body_id:
    folder = extconfig['data_dump_folder'] + os.sep + body_id + os.sep
    if not os.path.exists(folder):
      os.makedirs(folder)
    create_download_package(extconfig, db, fs, str(body['_id']))
  else:
    for body in db.body.find():
      folder = extconfig['data_dump_folder'] + os.sep + str(body['_id'])
      if not os.path.exists(folder):
        os.makedirs(folder)
      create_download_package(extconfig, db, fs, str(body['_id']))
  
