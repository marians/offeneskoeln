#!/usr/bin/env python
# encoding: utf-8

"""
    Generiert Thumbnails von allen Attachments
    
    TODO:
    - Prüfen, ob Dokument neuer ist als Thumbnail und ggf. Thumb neu produzieren.
    - Nur bei bestimmten Dateiendungen Thumbnail erzeugen
    
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

# Pfad zum Timeout-Script
# Das Script timeout ist ein Perl-Script. Es kommt von
# https://github.com/pshved/timeout
TIMEOUT_PATH = './timeout.pl'

# Pfad zum ImageMagick convert Tool
CONVERT_PATH = '/usr/bin/convert'

# Bei diesen Attachment-Endungen werden Thumbs generiert:
VALID_TYPES = ['jpg', 'pdf', 'tif', 'bmp', 'png', 'gif']

# Diese Größen (Höhe) werden generiert:
SIZES = [300, 600, 150]
SIZES = [300, 800, 150]

THUMB_SUFFIX = 'jpg'

MEMORY_LIMIT = 100000

CPU_TIME_LIMIT = 60

def generate_all_thumbs(attachments_folder, thumbs_folder):
    for root, dirs, files in os.walk(attachments_folder):
        for fname in files:
            file_id = get_id_from_file(fname)
            if file_id is not None:
                if not thumb_exists(file_id):
                    path = root + '/' + fname
                    generate_thumbs_for_file(file_id, path)
            
# returns numeric ID part from attachment file name
def get_id_from_file(filename):
    m = re.match(r'[a-z]*([0-9]+)\.[a-z]+', filename)
    if m is not None:
        return m.group(1)

# checks if thumbnail for file id already exists
def thumb_exists(file_id):
    base = config.THUMBS_PATH + '/' + subfolders_for_file_id(file_id)
    # without page number (single page files)
    for size in SIZES:
        path = base + '/' + file_id + '-' + str(size) + '.' + THUMB_SUFFIX
        if os.path.isfile(path):
            return True
    # with page number (multi page files) - checking only first (0)
    for size in SIZES:
        path = base + '/' + file_id + '-' + str(size) + '-0.' + THUMB_SUFFIX
        if os.path.isfile(path):
            return True
    return False

def subfolders_for_file_id(file_id):
    return file_id[-1] + '/' + file_id[-2]

def generate_thumbs_for_file(file_id, source_file):
    print source_file
    subpath = subfolders_for_file_id(file_id)
    if not os.path.exists(config.THUMBS_PATH + '/' + subpath):
        #print "Must create", config.THUMBS_PATH + '/' + subpath
        try:
            os.makedirs(config.THUMBS_PATH + '/' + subpath)
        except:
            print >> sys.stderr, "Could not create directory " + config.THUMBS_PATH + '/' + subpath
            sys.exit(1)
    for size in SIZES:
        dest_file = config.THUMBS_PATH + '/' + subpath + '/' + file_id + '-' + str(size) + '.' + THUMB_SUFFIX
        cmd = "%s -t %d -m %d %s -thumbnail x%d %s %s" % (TIMEOUT_PATH, 
            CPU_TIME_LIMIT, MEMORY_LIMIT, CONVERT_PATH, size, source_file, dest_file)
        output, error = subprocess.Popen(
            cmd.split(' '), stdout=subprocess.PIPE,
            stderr=subprocess.PIPE).communicate()
        if error is not None and error != '':
            print >> sys.stderr, "Could not create thumb for " + source_file + " size:" + str(size)
            #print >> sys.stderr, "Command: " + cmd
            print >> sys.stderr, error
            #sys.exit(1)

if __name__ == '__main__':
    generate_all_thumbs(config.ATTACHMENTS_PATH, config.THUMBS_PATH)
