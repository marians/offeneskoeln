# encoding: utf-8

"""
Erzeugt einen RSS-Feed mit den zuletzt hinzugefügten bzw. geänderten
Dokumenten (submissions).

Copyright (c) 2013 Marian Steinbach

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
from pymongo import MongoClient
from lxml import etree
import email.utils
import calendar
import urllib
from datetime import datetime

cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../city")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

# max Number of items
LIMIT = 100


def rfc1123date(value):
    """
    Gibt ein Datum (datetime) im HTTP Head-tauglichen Format (RFC 1123) zurück
    """
    tpl = value.timetuple()
    stamp = calendar.timegm(tpl)
    return email.utils.formatdate(timeval=stamp, localtime=False, usegmt=True)


def submission_url(identifier):
    url = cityconfig.BASE_URL
    url += 'dokumente/' + urllib.quote_plus(identifier) + '/'
    return url


def generate_channel():
    feed_url = cityconfig.BASE_URL + '/static/rss/' + cityconfig.RS + '_dokumente.xml'
    root = etree.Element("rss", version="2.0", nsmap={'atom': 'http://www.w3.org/2005/Atom'})
    channel = etree.SubElement(root, "channel")
    etree.SubElement(channel, "title").text = cityconfig.APP_NAME + ': Neue Dokumente'
    etree.SubElement(channel, "link").text = cityconfig.BASE_URL
    etree.SubElement(channel, "language").text = 'de-de'
    description = ("Neue oder geänderte Dokumente auf ".decode('utf-8')) + cityconfig.APP_NAME
    etree.SubElement(channel, "description").text = description
    etree.SubElement(channel, '{http://www.w3.org/2005/Atom}link',
        href=feed_url, rel="self", type="application/rss+xml")

    project = {
        'identifier': {'$exists': True},
        'title': {'$exists': True},
        'last_modified': {'$exists': True},
        "rs" : cityconfig.RS
    }
    # use latest item lastmod date as pubDate of the feed
    pub_date = None
    # iterate items
    for s in db.submissions.find(project).sort('last_modified', -1).limit(LIMIT):
        if pub_date is None:
            pub_date = s['last_modified']
        url = submission_url(s['identifier'])
        description = 'Art des Dokuments: ' + s['type'] + '<br />'
        description += 'Erstellt am: ' + s['date'].strftime('%d. %B %Y').decode('utf-8') + '<br />'
        description += 'Zuletzt geändert am: '.decode('utf-8') + s['last_modified'].strftime('%d. %B %Y') + '<br />'
        if 'sessions' in s:
            if len(s['sessions']) == 1:
                description += 'Beraten in: 1 Sitzung' + '<br />'
            else:
                description += 'Beraten in: ' + str(len(s['sessions'])) + ' Sitzungen' + '<br />'
        description += 'Anlagen: ' + str(len(s['attachments'])) + '<br />'
        item = etree.SubElement(channel, "item")
        etree.SubElement(item, "pubDate").text = rfc1123date(s['last_modified'])
        etree.SubElement(item, "title").text = s['title']
        etree.SubElement(item, "description").text = description
        etree.SubElement(item, "link").text = url.replace('%2F', '/')
        etree.SubElement(item, "guid").text = url.replace('%2F', '/')
    #failback if empty
    if pub_date is None:
        pub_date = datetime.now()
    etree.SubElement(channel, "pubDate").text = rfc1123date(pub_date)
    return etree.tostring(root, pretty_print=True)


def save_channel(xml):
    """
    Saves the output file. But only if it's different from the last one.
    Otherwise the old with it's last-modified-date is preserved, allowing
    for cached versions to be used (conditional get etc.).
    """
    overwrite = False
    path = config.BASE_PATH + '/static/rss/' + cityconfig.RS + '_dokumente.xml'
    if not os.path.exists(path):
        overwrite = True
    else:
        size = os.path.getsize(path)
        if size != len(xml):
            overwrite = True
        else:
            from hashlib import md5
            of = open(path, 'rb')
            old_xml = of.read()
            of.close()
            old_md5 = md5(old_xml).digest()
            new_md5 = md5(xml).digest()
            if old_md5 != new_md5:
                overwrite = True
    if overwrite:
        print "Writing latest RSS feed to %s" % path
        f = open(path, 'wb')
        f.write(xml)
        f.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generate Fulltext for given City Conf File')
    parser.add_argument(dest='city', help=("e.g. bochum"))
    options = parser.parse_args()
    city = options.city
    cityconfig = __import__(city)
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    xml = generate_channel()
    save_channel(xml)
