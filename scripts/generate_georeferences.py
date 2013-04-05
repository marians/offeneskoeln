# encoding: utf-8

"""
Finde Straßennamen in Texten und trage Geo-Referenzen
in die entsprechenden Dokumente ein

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
from pymongo import MongoClient
import re
import datetime


def generate_georeferences(db):
    """Generiert Geo-Referenzen für die gesamte submissions-Collection"""

    # Submissions ohne Geo-Referenzen
    query = {'georeferences_generated': {'$exists': False}}
    for doc in db.submissions.find(query):
        generate_georeferences_for_submission(doc['_id'], db)
    # TODO: Aktualisierte Dokumente berücksichtigen


def generate_georeferences_for_submission(doc_id, db):
    """
    Lädt die texte zu einer Submission, gleicht darin
    Straßennamen ab und schreibt das Ergebnis in das
    Submission-Dokument in der Datenbank.
    """
    submission = db.submissions.find_one({'_id': doc_id})
    text = ''
    if 'attachments' in submission and len(submission['attachments']) > 0:
        for a in submission['attachments']:
            text += " " + get_attachment_fulltext(a.id)
    if 'title' in submission:
        text += " " + submission['title']
    if 'subject' in submission:
        text += " " + submission['subject']
    text = text.encode('utf-8')
    result = match_streets(text)
    now = datetime.datetime.utcnow()
    update = {
        '$set': {
            'georeferences_generated': now
        }
    }
    if result != []:
        update['$set']['georeferences'] = result
        print ("Writing %d georeferences to submission %s" %
            (len(result), doc_id))
    db.submissions.update({'_id': doc_id}, update)


def get_attachment_fulltext(attachment_id):
    """

    """
    attachment = db.attachments.find_one({'_id': attachment_id})
    if 'fulltext' in attachment:
        return attachment['fulltext']
    return ''


def load_streets(path):
    """
    Lädt eine Straßenliste (ein Eintrag je Zeile UTF-8)
    in ein Dict. Dabei werden verschiedene Synonyme für
    Namen, die auf "straße" oder "platz" enden, angelegt.
    """
    nameslist = open(path, 'r').read().strip().split("\n")
    ret = {}
    pattern1 = re.compile(".*straße$")
    pattern2 = re.compile(".*Straße$")
    pattern3 = re.compile(".*platz$")
    pattern4 = re.compile(".*Platz$")
    for name in nameslist:
        ret[name.replace(' ', '-')] = name
        # Alternative Schreibweisen: z.B. straße => str.
        alternatives = []
        if pattern1.match(name):
            alternatives.append(name.replace('straße', 'str.'))
            alternatives.append(name.replace('straße', 'str'))
            alternatives.append(name.replace('straße', ' Straße'))
            alternatives.append(name.replace('straße', ' Str.'))
            alternatives.append(name.replace('straße', ' Str'))
        elif pattern2.match(name):
            alternatives.append(name.replace('Straße', 'Str.'))
            alternatives.append(name.replace('Straße', 'Str'))
            alternatives.append(name.replace(' Straße', 'straße'))
            alternatives.append(name.replace(' Straße', 'str.'))
            alternatives.append(name.replace(' Straße', 'str'))
        elif pattern3.match(name):
            alternatives.append(name.replace('platz', 'pl.'))
            alternatives.append(name.replace('platz', 'pl'))
        elif pattern4.match(name):
            alternatives.append(name.replace('Platz', 'Pl.'))
            alternatives.append(name.replace('Platz', 'Pl'))
        for alt in alternatives:
            ret[alt.replace(' ', '-')] = name
    return ret


def match_streets(text):
    """
    Findet alle Vorkommnisse einer Liste von Straßennamen
    in dem gegebenen String und gibt sie
    als Liste zurück
    """
    results = {}
    for variation in streets.keys():
        if variation in text:
            results[streets[variation]] = True
    return sorted(results.keys())


if __name__ == '__main__':
    streets = load_streets(config.STREETS_FILE)
    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    generate_georeferences(db)
