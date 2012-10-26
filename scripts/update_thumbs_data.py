#!/usr/bin/env python
# encoding: utf-8

"""
Schreibt Daten über Attachment-Thumbnails in die Datenbank

Für jede existierende Thumbnail-Datei wird ein Eintrag vorgenommen.

- Mit -v wird der versbose-Mode eingeschaltet
- Mit -a bzw --maxage <int> kann das maximale Dateialter in Tagen
  angegeben werden. Ältere Dateien werden ignoriert.
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
import re
import sys
import Image
import MySQLdb
import time
from optparse import OptionParser


def find_thumbs(thumbs_folder, maxage=-1):
    """
    Durchsucht durch den Thumbnail-Ordner
    """
    for root, dirs, files in os.walk(thumbs_folder):
        for fname in files:
            file_id = get_id_from_file(fname)
            if file_id is not None:
                path = root + os.sep + fname
                if maxage > -1:
                    age = get_file_age(path)
                    if age > maxage:
                        continue
                write_to_db(file_id, fname, path)


def get_file_age(path):
    st = os.stat(path)
    age_sec = time.time() - st.st_mtime
    return float(age_sec) / 86400.0


def check_database():
    """
    Prüft alle Einträge in der DB-Tabelle, ob die
    entsprechenden Thumbnail-Dateien vorhanden sind
    und entfernt bei Bedarf den Eintrag.
    """
    sql = "SELECT attachment_id, filename FROM %s" % config.DB_THUMBS_TABLE
    try:
        cursor.execute(sql)
    except MySQLdb.Error, e:
        sys.stderr.write("Error %d: %s\n" % (e.args[0], e.args[1]))
        return
    while (1):
        row = cursor.fetchone()
        if row == None:
            break
        path = (config.THUMBS_PATH + os.sep + subfolders_for_file_id(str(row['attachment_id'])) +
            os.sep + row['filename'])
        if not os.path.exists(path):
            if options.verbose:
                print "Thumbnail does not exist: " + path
            remove = 'DELETE FROM %s WHERE filename="%s"' % (config.DB_THUMBS_TABLE, row['filename'])
            cursor.execute(remove)


def subfolders_for_file_id(file_id):
    """Generates sub path like 1/2 based on file id"""
    return file_id[-1] + os.sep + file_id[-2]


def get_id_from_file(filename):
    """
    Gibt die numerische Attachment-ID innerhalb des Dateinamens zurück
    """
    m = re.match(r'([0-9]+)[-0-9]*\.[a-z]+', filename)
    if m is not None:
        return m.group(1)


def write_to_db(file_id, filename, path):
    """
    Schreibt zu einer Datei einen Thumbnail-Eintrag in die Datenbank.
    Wenn der Eintrag schon existiert, wird er aktualisiert.
    """
    global cursor
    try:
        im = Image.open(path)
    except IOError:
        sys.stderr.write("ERROR: Unreadable file " + path + "\n")
        return
    im.size[0], im.size[1]
    # get page number
    page = 0
    m = re.match(r'[0-9]+\-[0-9]+\-([0-9]+)\.[a-z]+', filename)
    if m is not None:
        page = m.group(1)
    if options.verbose:
        print filename, im.size[0], im.size[1], page
    sql = """INSERT INTO """ + config.DB_THUMBS_TABLE + """
        (attachment_id, filename, width, height, page) VALUES
        (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE filename=%s, width=%s, height=%s, page=%s"""
    cursor.execute(sql, (file_id, filename, im.size[0], im.size[1],
        page, filename, im.size[0], im.size[1], page))


if __name__ == '__main__':
    parser = OptionParser()
    # Kommandozeilen-Optionen
    parser.add_option("-v", action="store_true",
        dest="verbose", default=False)
    parser.add_option("-a", "--maxage", dest="maxage",
        help="add entries for files only if newer than MAXAGE days", metavar="MAXAGE", default="-1")
    (options, args) = parser.parse_args()
    conn = MySQLdb.connect(host=config.DB_HOST, user=config.DB_USER,
        passwd=config.DB_PASS, db=config.DB_NAME)
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    if options.verbose:
        print "Checking for orphaned database entries..."
    check_database()
    if options.verbose:
        print "Checking for new thumbnail files..."
    find_thumbs(config.THUMBS_PATH, int(options.maxage))
