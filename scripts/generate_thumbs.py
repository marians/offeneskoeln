#!/usr/bin/env python
# encoding: utf-8

"""
Generiert Thumbnails (Vorschaubilder) von allen Attachments im
Attachments-Ordner, sofern möglich.

Abhängigkeiten:
- ImageMagick
- timeout.pl - siehe https://github.com/pshved/timeout


TODO:
- Prüfen, ob Dokument neuer ist als Thumbnail und ggf. Thumb neu produzieren.
- Nur bei bestimmten Dateiendungen Thumbnail erzeugen
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
import subprocess


STATS = {
    'attachments_ohne_thumbnails_vorher': 0,
    'attachments_erfolgreich': 0
}

# Auf False setzen, um die Thumbs-Generierung für
# Debugging-Zwecke zu deaktivieren
GENERATE = True


def generate_all_thumbs(attachments_folder, thumbs_folder):
    """Generiert alle Thumbnails fuer einen Ordner"""
    for root, dirs, files in os.walk(attachments_folder):
        for fname in files:
            file_id = get_id_from_file(fname)
            if file_id is None:
                continue
            # Teste, ob Thumbnail schon existiert
            for size in config.THUMBNAILS_SIZES:
                if thumb_exists(file_id, size):
                    continue
                STATS['attachments_ohne_thumbnails_vorher'] += 1
                if not GENERATE:
                    continue
                path = root + '/' + fname
                result = generate_thumbs_for_file(file_id, path, size)
                if result:
                    STATS['attachments_erfolgreich'] += 1


def get_id_from_file(filename):
    """returns numeric ID part from attachment file name"""
    m = re.match(r'[a-z]*([0-9]+)\.[a-z]+', filename)
    if m is not None:
        return m.group(1)


def thumb_exists(file_id, size):
    """checks if thumbnail for given file id and size already exists"""
    base = config.THUMBS_PATH + '/' + subfolders_for_file_id(file_id)
    # without page number (single page files)
    path = base + '/' + file_id + '-' + str(size) + '.' + config.THUMBNAILS_SUFFIX
    #print "Checking for", path
    if not os.path.isfile(path):
        # first variant not found. Now check for second variant.
        # with page number (multi page files) - checking only first (0)
        path = base + '/' + file_id + '-' + str(size) + '-0.' + config.THUMBNAILS_SUFFIX
        #print "Checking for", path
        if not os.path.isfile(path):
            # Both variants not found
            return False
    return True


def subfolders_for_file_id(file_id):
    """Generates sub path like 1/2 based on file id"""
    return file_id[-1] + '/' + file_id[-2]


def generate_thumbs_for_file(file_id, source_file, size):
    """
    Generiert Thumbnails fuer eine bestimmte Source-Datei
    und eine bestimmte Groesse
    """
    #print source_file
    subpath = subfolders_for_file_id(file_id)
    if not os.path.exists(config.THUMBS_PATH + '/' + subpath):
        try:
            os.makedirs(config.THUMBS_PATH + '/' + subpath)
        except:
            print >> sys.stderr, "Could not create directory " + config.THUMBS_PATH + '/' + subpath
            sys.exit(1)
    dest_file = config.THUMBS_PATH + '/' + subpath + '/' + file_id + '-' + str(size) + '.' + config.THUMBNAILS_SUFFIX
    print "Creating", size, dest_file
    cmd = "%s -t %d -m %d %s -thumbnail x%d %s %s" % (TIMEOUT_CMD, config.THUMBNAILS_CPU_TIME_LIMIT, config.THUMBNAILS_MEMORY_LIMIT, CONVERT_CMD, size, source_file, dest_file)
    output, error = subprocess.Popen(
        cmd.split(' '), stdout=subprocess.PIPE,
        stderr=subprocess.PIPE).communicate()
    if error is not None and error != '':
        print >> sys.stderr, "Could not create thumb for " + source_file + " size:" + str(size)
        #print >> sys.stderr, "Command: " + cmd
        print >> sys.stderr, error
        return False
    else:
        return True

if __name__ == '__main__':
    generate_all_thumbs(config.ATTACHMENTS_PATH, config.THUMBS_PATH)
    print STATS
