#!/usr/bin/env python
# encoding: utf-8

"""
    Schreibt Daten über Attachment-Thumbnails in die Datenbank
    
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

# Schreibt Info über Thumbnails in die Datenbank

# Tabelle: config.DB_THUMBS_TABLE

def find_thumbs(thumbs_folder):
    for root, dirs, files in os.walk(thumbs_folder):
        for fname in files:
            #print fname
            file_id = get_id_from_file(fname)
            if file_id is not None:
                path = root + '/' + fname
                write_to_db(file_id, fname, path)
            
# returns numeric ID part from attachment file name
def get_id_from_file(filename):
    m = re.match(r'([0-9]+)[-0-9]*\.[a-z]+', filename)
    if m is not None:
        return m.group(1)

def write_to_db(file_id, filename, path):
    global cursor
    im = Image.open(path)
    im.size[0], im.size[1]
    # get page number
    page = 0
    m = re.match(r'[0-9]+\-[0-9]+\-([0-9]+)\.[a-z]+', filename)
    if m is not None:
        page = m.group(1)
    print file_id, filename, im.size[0], im.size[1], page
    sql = """INSERT INTO """ + config.DB_THUMBS_TABLE + """ 
        (attachment_id, filename, width, height, page) VALUES
        (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE filename=%s, width=%s, height=%s, page=%s"""
    cursor.execute(sql, (file_id, filename, im.size[0], im.size[1], page, filename, im.size[0], im.size[1], page))

if __name__ == '__main__':
    conn = MySQLdb.connect (host=config.DB_HOST, user=config.DB_USER, passwd=config.DB_PASS, db=config.DB_NAME)
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    find_thumbs(config.THUMBS_PATH)
    