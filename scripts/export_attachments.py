# encoding: utf-8

"""
Erstellt ein tar.bz2 Paket der Anhänge eines bestimmten Datumsbereichs.
Dabei wird das Änderungsdatum der Datei berücksichtigt - also der
Zeitpunkt, zu dem die Datei abgerufen wurde.

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
from webapp import date_range
from pymongo import MongoClient
import gridfs
import subprocess

cmd_subfolder = os.path.realpath(os.path.abspath(os.path.join(os.path.split(inspect.getfile( inspect.currentframe() ))[0],"../city")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)

def save_file(file_id, path):
    """
    Copy a file from MongoDB GridFS to a local file system path
    """
    if options.verbose:
        print "%s, %s" % (file_id, path)
    file_doc = fs.get(file_id)
    tempf = open(path, 'wb')
    tempf.write(file_doc.read())
    tempf.close()
    return path


def create_download_package(daterange, folder):
    """
    daterange: a datetime tuple compatible string
    folder: The target folder and final output filename prefix
    """
    start = datetime.datetime(daterange[0].year, daterange[0].month, daterange[0].day, 0, 0, 0)
    end = datetime.datetime(daterange[1].year, daterange[1].month, daterange[1].day, 23, 59, 59)
    #print start, end
    query = {
        'uploadDate': {
        '$gt': start,
        '$lt': end,
        "rs" : cityconfig.RS
    }}
    for afile in db.fs.files.find(query):
        fid = afile['_id']
        path = folder + os.sep + afile['filename']
        save_file(fid, path)
    execute('tar cjf %s.tar.bz2 %s' % (folder, folder))
    execute('rm -r %s' % folder)


def execute(cmd):
    output, error = subprocess.Popen(
        cmd.split(' '), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    if error is not None and error.strip() != '':
        print >> sys.stderr, "Command: " + cmd
        print >> sys.stderr, "Error: " + error


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Create a package of attachment files for a certain date range')
    #city
    parser.add_argument(dest='city', help=("e.g. bochum"))
    # date range default: current month
    parser.add_argument(dest='daterange', help=("e.g. 2010-2011 or 201208-201209."))
    parser.add_argument('--verbose', '-v', action='count', default=0, dest="verbose",
        help="Give verbose output")
    output_name_default = datetime.datetime.now().strftime('attachments_%Y-%m-%d-%H%M') + '_<daterange>'
    parser.add_argument('--name', '-n', dest="output_name",
        help='Name prefix for the output file. Default: %s' % output_name_default)
    options = parser.parse_args()
    city = options.city
    cityconfig = __import__(city)

    if options.output_name is None:
        options.output_name = 'attachments_' + options.daterange

    daterange = date_range.to_dates(options.daterange)
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    fs = gridfs.GridFS(db)

    tempdir = os.mkdir(options.output_name)

    #print (daterange, options.output_name)
    create_download_package(daterange, options.output_name)
