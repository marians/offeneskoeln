#!/usr/bin/env python
# encoding: utf-8

"""
Generiert Thumbnails (Vorschaubilder) von allen Datei-Anhängen in
der Datenbank.

Datenstruktur in einem Dokument der collection "attachments":

{
    _id: ...,
    thumbnails: {
        800: [
            {
                page: 1,
                width: 565,
                height: 800
            },
            {
                page: 2,
                width: 565,
                height: 800
            }
        ],
        300: [...],
        150: [...]
    },
    thumbnails_generated: ISODate("2013-04-04T14:45:32.242Z"),
    ...
}

Die Dateien werden in einem Verzeichnis abgelegt, dass aus der _id des attachments
und der Höhe des Thumbnails gebildet wird. Für die _id "515d920cc9791e05b5047e8f"
lauten beispielhafte Pfade:

config.THUMBS_PATH + 'f/8/515d920cc9791e05b5047e8f/800/1.png'
config.THUMBS_PATH + 'f/8/515d920cc9791e05b5047e8f/300/1.png'
config.THUMBS_PATH + 'f/8/515d920cc9791e05b5047e8f/150/1.png'
...

Dabei wird der Präfix f/8 aus den lezten beiden Zeichen der _id gebildet.


Besondere Abhängigkeiten:
- Ghostscript

TODO:
- Prüfen, ob die Thumbnails für alle Seiten vorhanden sind. Es können einzelne fehlen.
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
import tempfile
import subprocess
from pymongo import MongoClient
import gridfs
import shutil
from PIL import Image
import datetime
import time
import threading
import argparse


STATS = {
    'attachments_without_thumbs': 0,
    'attachments_with_outdated_thumbs': 0,
    'thumbs_created_for_n_attachments': 0,
    'thumbs_created': 0,
    'thumbs_not_created': 0,
    'ms_saving_tempfile': 0,
    'ms_creating_maxsize': 0,
    'ms_creating_thumb': 0,
    'num_saving_tempfile': 0,
    'num_creating_maxsize': 0,
    'num_creating_thumb': 0
}

# Aktiviert die Zeitmessung
TIMING = True
TIMEOUT = 10


def generate_thumbs(db, thumbs_folder, timeout):
    """Generiert alle Thumbnails für die gesamte attachments-Collection"""
    # Attachments mit veralteten Thumbnails
    query = {
        'thumbnails_generated': {'$exists': True},
        'depublication': {'$exists': False}
    }
    # Attachments mit veralteten Thumbnails
    for doc in db.attachments.find(query, timeout=False):
        # Dateiinfo abholen
        filedoc = db.fs.files.find_one({'_id': doc['file'].id})
        if filedoc['uploadDate'] > doc['thumbnails_generated']:
            # Thumbnails müssen erneuert werden
            STATS['attachments_with_outdated_thumbs'] += 1
            generate_thumbs_for_attachment(doc['_id'], db, timeout)
    # Attachments ohne Thumbnails
    query = {
        'thumbnails': {'$exists': False},
        'depublication': {'$exists': False}
    }
    for doc in db.attachments.find(query, timeout=False):
        if get_file_suffix(doc['filename']) in config.THUMBNAILS_VALID_TYPES:
            STATS['attachments_without_thumbs'] += 1
            generate_thumbs_for_attachment(doc['_id'], db, timeout)


def get_file_suffix(filename):
    """Return suffix of file (part after last period)"""
    return filename.split('.')[-1]


def subfolders_for_attachment(attachment_id):
    """Generates sub path like 1/2 based on attachment id"""
    attachment_id = str(attachment_id)
    return os.path.join(attachment_id[-1],
        attachment_id[-2],
        attachment_id)


def generate_thumbs_for_attachment(attachment_id, db, timeout):
    """
    Generiert alle Thumbnails fuer ein bestimmtes Attachment
    """
    # temporaere Datei des Attachments anlegen
    if TIMING:
        start = milliseconds()
    doc = db.attachments.find_one({'_id': attachment_id}, {'file': 1, 'filename': 1})
    #print "Trying to get file id", doc['file'].id
    file_doc = fs.get(doc['file'].id)
    temppath = tempdir + os.sep + doc['filename']
    print "Creating thumb - attachment_id=%s, filename=%s" % (str(attachment_id), doc['filename'])
    tempf = open(temppath, 'wb')
    tempf.write(file_doc.read())
    tempf.close()
    if TIMING:
        after_file_write = milliseconds()
        file_write_duration = after_file_write - start
        STATS['ms_saving_tempfile'] += file_write_duration
        STATS['num_saving_tempfile'] += 1
    subpath = subfolders_for_attachment(attachment_id)
    abspath = config.THUMBS_PATH + os.sep + subpath
    if not os.path.exists(abspath):
        os.makedirs(abspath)

    # TODO: Only do this for .pdf files
    #  create maximum size PNGs first
    max_folder = abspath + os.sep + 'max'
    if not os.path.exists(max_folder):
            os.makedirs(max_folder)
    file_path = max_folder + os.sep + '%d.png'
    cmd = ('%s -dQUIET -dSAFER -dBATCH -dNOPAUSE -sDisplayHandle=0 -sDEVICE=png16m -r100 -dTextAlphaBits=4 -sOutputFile=%s -f %s' %
            (config.GS_CMD, file_path, temppath))
    pm = ProcessMonitor(cmd)
    result = pm.run(timeout=timeout)

    if TIMING:
        after_maxthumbs = milliseconds()
        maxthumbs_duration = after_maxthumbs - after_file_write
        STATS['ms_creating_maxsize'] += maxthumbs_duration
        STATS['num_creating_maxsize'] += 1

    if result == False:
        # break here
        STATS['thumbs_not_created'] += 1
        os.unlink(temppath)
        return

    thumbnails = {}
    for size in config.THUMBNAILS_SIZES:
        thumbnails[str(size)] = []

    ### create thumbs based on large pixel version

    # get highest page number
    maxfiles = os.listdir(max_folder)
    max_pagenum = 0
    for mfile in maxfiles:
        num = int(mfile.split('.')[0])
        max_pagenum = max(max_pagenum, num)

    for pagenum in range(1, max_pagenum + 1):
        path = max_folder + os.sep + str(pagenum) + '.png'
        if not os.path.exists(path):
            sys.stderr.write('Page thumbnail missing: page %d' % pagenum)
            continue
        im = Image.open(path)
        im = conditional_to_greyscale(im)
        (owidth, oheight) = im.size
        for size in config.THUMBNAILS_SIZES:
            if TIMING:
                before_thumb = milliseconds()
            size_folder = abspath + os.sep + str(size)
            if not os.path.exists(size_folder):
                os.makedirs(size_folder)
            out_path = size_folder + os.sep + str(pagenum) + '.' + config.THUMBNAILS_SUFFIX
            (width, height) = scale_width_height(size, owidth, oheight)
            #print (width, height)
            # Two-way resizing
            resizedim = im
            if oheight > (height * 2.5):
                # generate intermediate image with double size
                resizedim = resizedim.resize((width * 2, height * 2), Image.NEAREST)
            resizedim = resizedim.resize((width, height), Image.ANTIALIAS)
            resizedim.save(out_path)
            thumbnails[str(size)].append({
                'page': pagenum,
                'width': width,
                'height': height,
                'filesize': os.path.getsize(out_path)
            })
            if os.path.exists(out_path):
                STATS['thumbs_created'] += 1
            else:
                sys.stderr.write("ERROR: Thumbnail has not been saved in %s.\n" % out_path)
                STATS['thumbs_not_created'] += 1
            if TIMING:
                after_thumb = milliseconds()
                thumb_duration = after_thumb - before_thumb
                STATS['ms_creating_thumb'] += thumb_duration
                STATS['num_creating_thumb'] += 1
    # delete temp file
    os.unlink(temppath)
    # delete max size images
    shutil.rmtree(max_folder)
    now = datetime.datetime.utcnow()
    db.attachments.update({'_id': attachment_id}, {
        '$set': {
            'thumbnails': thumbnails,
            'thumbnails_generated': now,
            'last_modified': now
        }
    })
    STATS['thumbs_created_for_n_attachments'] += 1


def conditional_to_greyscale(image):
    """
    Convert the image to greyscale if the image information
    is greyscale only
    """
    bands = image.getbands()
    if len(bands) >= 3:
        # histogram for all bands concatenated
        hist = image.histogram()
        if len(hist) >= 768:
            hist1 = hist[0:256]
            hist2 = hist[256:512]
            hist3 = hist[512:768]
            #print "length of histograms: %d %d %d" % (len(hist1), len(hist2), len(hist3))
            if hist1 == hist2 == hist3:
                #print "All histograms are the same!"
                return image.convert('L')
    return image


def scale_width_height(height, original_width, original_height):
    factor = float(height) / float(original_height)
    width = int(round(factor * original_width))
    return (width, height)


def milliseconds():
    """Return current time as milliseconds int"""
    return int(round(time.time() * 1000))


def print_stats():
    for key in STATS.keys():
        print "%s: %d" % (key, STATS[key])


class ProcessMonitor(object):
    """
    Gratefully taken from
    http://stackoverflow.com/a/4825933/1228491
    """
    def __init__(self, cmd):
        self.cmd = cmd
        self.process = None

    def run(self, timeout):
        def target():
            self.process = subprocess.Popen(self.cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            output, error = self.process.communicate()
            if error is not None and error.strip() != '':
                sys.stderr.write("Command: %s\n" % self.cmd)
                sys.stderr.write("Error: %s\n" % error)
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            sys.stderr.write("Process taking too long -- terminating\n")
            self.process.terminate()
            thread.join()
            # Process has been interrupted
            return False
        return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate thumbnails for attachment files')
    parser.add_argument('--timeout', dest='timeout', default=TIMEOUT, type=int,
        help='Number of seconds to wait for thumbnail generation per attachment')
    args = parser.parse_args()
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    fs = gridfs.GridFS(db)
    tempdir = tempfile.mkdtemp()
    generate_thumbs(db, config.THUMBS_PATH, timeout=args.timeout)
    os.rmdir(tempdir)
    print_stats()
