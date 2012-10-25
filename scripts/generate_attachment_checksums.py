# encoding: utf-8

"""
Erzeugt für alle Attachments, wo dieser noch fehlt, den sha1_checksum
Eintrag in der Datenbank.

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
import hashlib
import os
import sys
import MySQLdb
import re


def generate_all_hashes(attachments_folder):
    for root, dirs, files in os.walk(attachments_folder):
        for fname in files:
            attachment_id = get_id_from_file(fname)
            if attachment_id is None:
                continue
            if has_checksum(attachment_id):
                continue
            path = root + '/' + fname
            sha_hash = file_sha1(path)
            if sha_hash is not None:
                print attachment_id, sha_hash
                store_hash(attachment_id, sha_hash)


def get_id_from_file(filename):
    m = re.match(r'[a-z]*([0-9]+)\.[a-z]+', filename)
    if m is not None:
        return m.group(1)


def file_sha1(path):
    """
    Erzeugt SHA1 Prüfsumme der Datei
    """
    sha = hashlib.sha1()
    fh = open(path, 'r')
    content = fh.read()
    sha.update(content)
    fh.close()
    return sha.hexdigest()


def store_hash(file_id, sha_hash):
    sql = 'UPDATE attachments SET sha1_checksum=%s WHERE attachment_id=%s'
    cursor.execute(sql, (sha_hash, file_id))


def has_checksum(attachment_id):
    sql = 'SELECT sha1_checksum FROM attachments WHERE attachment_id=%s'
    cursor.execute(sql, (attachment_id))
    row = cursor.fetchone()
    if row is not None:
        if row['sha1_checksum'] is None:
            return False
        return True
    else:
        sys.stderr.write("Fehler: Attachment" + str(attachment_id)
            + "ist nicht in Datenbank\n")

if __name__ == '__main__':
    conn = MySQLdb.connect(host=config.DBHOST, user=config.DBUSER,
        passwd=config.DBPASS, db=config.DBNAME)
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    generate_all_hashes(config.ATTACHMENTS_PATH)
