#!/usr/bin/env python
# encoding: utf-8

"""
Generiert XML Sitemaps fuer files
"""

"""
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

import config
import os
import inspect
import argparse
import datetime
import subprocess
from pymongo import MongoClient
import urllib
import config
from bson import DBRef


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

def execute(cmd):
  output, error = subprocess.Popen(
    cmd.split(' '), stdout=subprocess.PIPE,
    stderr=subprocess.PIPE).communicate()
  if error is not None and error.strip() != '':
    print >> sys.stderr, "Command: " + cmd
    print >> sys.stderr, "Error: " + error

def generate_sitemaps(config):
  limit = 50000
  sitemaps = []
  urls = []
  bodies = []
  
  # tidy up
  cmd = "rm -f %s/*.gz" % config['sitemap_folder']
  execute(cmd)
  
  # gather bodies
  for body in db.body.find({}):
    bodies.append(body['_id'])
  print bodies
  
    # gather file URLs
  for body in bodies:
    for file in db.file.find({'body': DBRef('body', body), 'depublication': {'$exists': False}}):
      fileentry = db.fs.files.find_one(file['file'].id)
      thisfile = {
        'path': "%s/oparl/file/%s/downloadUrl" % (config['base_url'], file['_id']),
        'lastmod': fileentry['uploadDate']
      }
      urls.append(thisfile)

    # create sitemap(s) with individual attachment URLs
    sitemap_count = 1
    while len(urls) > 0:
      shortlist = []
      while len(shortlist) < limit and len(urls) > 0:
        shortlist.append(urls.pop(0))
      sitemap_name = 'files_%s_%d' % (body, sitemap_count)
      generate_sitemap(shortlist, sitemap_name)
      sitemaps.append(sitemap_name)
      sitemap_count += 1

  urls = []
  for body in bodies:
    # gather submission URLs
    for paper in db.paper.find({'body': DBRef('body', body)}):
      thisfile = {
        'path': "%s/paper/%s" % (config['base_url'], paper['_id']),
        'lastmod': paper['lastModified']
      }
      urls.append(thisfile)

    # create sitemap(s) with individual attachment URLs
    sitemap_count = 1
    while len(urls) > 0:
      shortlist = []
      while len(shortlist) < limit and len(urls) > 0:
        shortlist.append(urls.pop(0))
      sitemap_name = 'papers_%s_%d' % (body, sitemap_count)
      print sitemap_name
      generate_sitemap(shortlist, sitemap_name)
      sitemaps.append(sitemap_name)
      sitemap_count += 1


  # Create meta-sitemap
  meta_sitemap_path = config['sitemap_folder'] + os.sep + 'sitemap.xml'
  f = open(meta_sitemap_path, 'w')
  f.write("""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""")
  for sitemap_name in sitemaps:
    f.write("""\n  <sitemap>
      <loc>%s_%s.xml.gz</loc>
  </sitemap>""" % (config['sitemap_folder'], sitemap_name))
  f.write("\n</sitemapindex>\n")
  f.close()


def generate_sitemap(files, name):
  sitemap_path = (config['sitemap_folder'] + os.sep + name + '.xml')
  f = open(sitemap_path, 'w')
  f.write("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""")
  for entry in files:
    f.write("""\n  <url>
    <loc>%s</loc>
    <lastmod>%s</lastmod>
  </url>""" % (entry['path'], entry['lastmod'].strftime('%Y-%m-%d')))
  f.write("</urlset>\n")
  f.close()
  cmd = "gzip %s" % sitemap_path
  execute(cmd)


if __name__ == '__main__':
  connection = MongoClient(config.MONGO_HOST, config.MONGO_PORT)
  db = connection[config.MONGO_DBNAME]
  config = get_config(db)
  generate_sitemaps(config)
