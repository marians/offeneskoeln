#!/usr/bin/env python
# encoding: utf-8

"""
Generiert XML Sitemaps fuer attachments
"""

"""
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
import datetime
import subprocess
from pymongo import MongoClient
import urllib

cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../city")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

def execute(cmd):
    output, error = subprocess.Popen(
        cmd.split(' '), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    if error is not None and error.strip() != '':
        print >> sys.stderr, "Command: " + cmd
        print >> sys.stderr, "Error: " + error


def attachment_url(attachment_id, filename=None, extension=None):
    if filename is not None:
        extension = filename.split('.')[-1]
    return cityconfig.ATTACHMENT_DOWNLOAD_URL % (attachment_id, extension)


def submission_url(identifier):
    url = cityconfig.BASE_URL
    url += 'dokumente/' + urllib.quote_plus(identifier) + '/'
    return url


def generate_sitemaps():
    limit = 50000
    sitemaps = []
    urls = []
    # gather attachment URLs
    for attachment in db.attachments.find({"rs" : cityconfig.RS}):
        fileentry = db.fs.files.find_one(attachment['file'].id)
        thisfile = {
            'path': attachment_url(attachment['_id'], filename=attachment['filename']),
            'lastmod': fileentry['uploadDate']
        }
        #print thisfile
        urls.append(thisfile)

    # create sitemap(s) with individual attachment URLs
    sitemap_count = 1
    while len(urls) > 0:
        shortlist = []
        # TODO: this could probably be done with slice
        while len(shortlist) < limit and len(urls) > 0:
            shortlist.append(urls.pop(0))
        sitemap_name = 'attachments_%d' % sitemap_count
        generate_sitemap(shortlist, sitemap_name)
        sitemaps.append(sitemap_name)
        sitemap_count += 1

    urls = []
    # gather submission URLs
    for submission in db.submissions.find():
        thisfile = {
            'path': submission_url(submission['identifier']),
            'lastmod': submission['last_modified']
        }
        #print thisfile
        urls.append(thisfile)

    # create sitemap(s) with individual attachment URLs
    sitemap_count = 1
    while len(urls) > 0:
        shortlist = []
        # TODO: this could probably be done with slice
        while len(shortlist) < limit and len(urls) > 0:
            shortlist.append(urls.pop(0))
        sitemap_name = 'submissions_%d' % sitemap_count
        generate_sitemap(shortlist, sitemap_name)
        sitemaps.append(sitemap_name)
        sitemap_count += 1


    # Create meta-sitemap
    meta_sitemap_path = config.SITEMAP_FOLDER + os.sep + cityconfig.RS + '.xml'
    f = open(meta_sitemap_path, 'w')
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""")
    for sitemap_name in sitemaps:
        f.write("""\n   <sitemap>
            <loc>%ssitemap/%s_%s.xml.gz</loc>
        </sitemap>\n""" % (cityconfig.STATIC_URL, cityconfig.RS, sitemap_name))
    f.write("</sitemapindex>\n")
    f.close()


def generate_sitemap(files, name):
    sitemap_path = (config.SITEMAP_FOLDER + os.sep + cityconfig.RS + '_' + name + '.xml')
    f = open(sitemap_path, 'w')
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""")
    for entry in files:
        f.write("""\n<url>
            <loc>%s</loc>
            <lastmod>%s</lastmod>
        </url>""" % (entry['path'], entry['lastmod'].strftime('%Y-%m-%d')))
    f.write("</urlset>\n")
    f.close()
    cmd = "rm %s.gz" % sitemap_path
    execute(cmd)
    cmd = "gzip %s" % sitemap_path
    execute(cmd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate Fulltext for given City Conf File')
    parser.add_argument(dest='city', help=("e.g. bochum"))
    options = parser.parse_args()
    city = options.city
    cityconfig = __import__(city)
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    generate_sitemaps()
