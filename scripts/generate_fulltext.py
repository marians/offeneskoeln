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

import config
import os
import tempfile
import sys
import subprocess
from pymongo import MongoClient
import gridfs
import datetime
import time


STATS = {
    'attachments_without_fulltext': 0,
    'attachments_with_outdated_fulltext': 0,
    'fulltext_created': 0,
    'fulltext_not_created': 0
}


def generate_fulltext(db):
    """Generiert Volltexte für die gesamte attachments-Collection"""

    # Attachments mit veralteten Volltexten
    query = {'fulltext_generated': {'$exists': True}}
    for doc in db.attachments.find(query):
        # Dateiinfo abholen
        filedoc = db.fs.files.find_one({'_id': doc['file'].id})
        if filedoc['uploadDate'] > doc['fulltext_generated']:
            # Volltext muss erneuert werden
            STATS['attachments_with_outdated_fulltext'] += 1
            generate_fulltext_for_attachment(doc['_id'], db)

    # Attachments ohne Volltext
    query = {'fulltext_generated': {'$exists': False}}
    for doc in db.attachments.find(query):
        STATS['attachments_without_fulltext'] += 1
        generate_fulltext_for_attachment(doc['_id'], db)


def store_tempfile(attachment_id, db):
    doc = db.attachments.find_one({'_id': attachment_id}, {'file': 1, 'filename': 1})
    file_doc = fs.get(doc['file'].id)
    temppath = tempdir + os.sep + doc['filename']
    tempf = open(temppath, 'wb')
    tempf.write(file_doc.read())
    tempf.close()
    return temppath


def generate_fulltext_for_attachment(attachment_id, db):
    """
    Generiert alle Thumbnails fuer ein bestimmtes Attachment
    """
    # temporaere Datei des Attachments anlegen
    print "Processing attachment_id=%s" % (str(attachment_id))
    path = store_tempfile(attachment_id, db)

    cmd = config.PDFTOTEXT_CMD + ' -nopgbrk -enc UTF-8 ' + path + ' -'
    text = execute(cmd)
    if text is not None:
        text = text.strip()
        text = text.decode('utf-8')

    # delete temp file
    os.unlink(path)
    now = datetime.datetime.utcnow()
    update = {
        '$set': {
            'fulltext_generated': now,
            'last_modified': now
        }
    }
    if text is None or text == '':
        STATS['fulltext_not_created'] += 1
    else:
        update['$set']['fulltext'] = text
        STATS['fulltext_created'] += 1
    db.attachments.update({'_id': attachment_id}, update)


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
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    fs = gridfs.GridFS(db)
    tempdir = tempfile.mkdtemp()
    generate_fulltext(db)
    os.rmdir(tempdir)
    print_stats()
