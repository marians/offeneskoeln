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

import config
import os
import datetime
from stat import *
import subprocess


def generate_sitemaps(attachments_folder):
    files = get_file_info(attachments_folder)
    limit = 50000
    sitemap_count = 1
    while len(files) > 0:
        shortlist = []
        while len(shortlist) < limit and len(files) > 0:
            shortlist.append(files.pop(0))
        generate_sitemap(shortlist, sitemap_count)
        #print len(shortlist)
        sitemap_count += 1
    meta_sitemap_path = config.ATTACHMENTS_PATH + '/sitemap.xml'
    f = open(meta_sitemap_path, 'w')
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
        <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""")
    for n in range(1, sitemap_count):
        f.write("""\n   <sitemap>
            <loc>http://offeneskoeln.de/attachments/sitemap_%d.xml.gz</loc>
        </sitemap>\n""" % n)
    f.write("</sitemapindex>\n")
    f.close()


def generate_sitemap(files, counter):
    sitemap_path = (config.ATTACHMENTS_PATH + '/' +
        'sitemap_' + str(counter) + '.xml')
    f = open(sitemap_path, 'w')
    f.write("""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""")
    for entry in files:
        f.write("""\n<url>
            <loc>http://offeneskoeln.de%s</loc>
            <lastmod>%s</lastmod>
        </url>""" % (entry['path'], entry['lastmod'].strftime('%Y-%m-%d')))
    f.write("</urlset>\n")
    f.close()
    cmd = "rm %s.gz" % sitemap_path
    output, error = subprocess.Popen(
        cmd.split(' '), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    #print output, error
    cmd = "gzip %s" % sitemap_path
    output, error = subprocess.Popen(
        cmd.split(' '), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    #print output, error


def get_file_info(startpath):
    outfiles = []
    for root, dirs, files in os.walk(startpath):
        webroot = root[len(config.WWW_PATH):]
        for fname in files:
            fullpath = root + '/' + fname
            path = webroot + '/' + fname
            outfiles.append({
                'path': path,
                'lastmod': datetime.datetime.fromtimestamp(os.stat(fullpath).st_mtime)
            })
    return outfiles

if __name__ == '__main__':
    generate_sitemaps(config.ATTACHMENTS_PATH)

