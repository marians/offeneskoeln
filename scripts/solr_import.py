#!/usr/bin/env python
# encoding: utf-8

"""
Datenimport für die Solr-Suche

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
import re
from datastore import DataStore
import solr
import config
from optparse import OptionParser
import datetime
import MySQLdb


def unique(list):
    """
    Entfernt doppelt vorkommende Werte aus einer Liste. Die Reihenfolge
    der Elemente wird dabei nicht berücksichtigt.
    """
    keys = {}
    for e in list:
        keys[e] = True
    return keys.keys()


def normalize_text(text):
    """
    Entfernt unerwünschte Zeichen aus einem Unicode-Text,
    wie z.B. doppelte Leerzeichen, Zeilenumbrüche, etc.
    """
    if text is None:
        return None
    text = text.replace("\r\n", ' ')
    text = text.replace("\n", ' ')
    text = text.replace("\r", ' ')
    text = ''.join(c for c in text if ord(c) >= 32)
    text = re.sub(r'[[:cntrl:]]+', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = text.strip()
    return text


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


def match_streets(streets, text):
    """
    Findet alle Vorkommnisse einer Liste von Straßennamen
    in dem gegebenen String (utf8-kodiert) und gibt sie
    als Liste zurück
    TODO: An neue Struktur von streets anpassen
    """
    text = text.replace('str.', 'straße')
    text = text.replace('Str.', 'Straße')
    text = text.replace('pl.', 'platz')
    results = []
    for variation in streets.keys():
        if text.find(variation) != -1:
            results.append(streets[variation])
    if len(results) == 0:
        return None
    return results


def normalize_doctype(dtype):
    """
    Ersetzt eine Vielzahl von unterschiedlichen Namen für Vorlagen-Typen
    in eine der folgenden Entsprechungen:
    - Anfrage
    - Antrag
    - Beschlussvorlage
    - Dringlichkeitsvorlage
    - Dringlichkeitsantrag
    - Mitteilung

    Es sollten sich unter anderem die folgenden
    Zuweisungen ergeben:

    Anfrage nach § 4 -> Anfrage
    Anfrage nach § 4 BV2 (Grüne) -> Anfrage
    Anfrage nach § 4 BV6 (Grüne) -> Anfrage
    Anfrage nach § 4 der GeschO des Rates -> Anfrage
    Antrag -> Antrag
    Antrag auf eine Aktuelle Stunde nach § 5 -> Antrag
    Antrag nach § 12 (Dringlichkeitsantrag) -> Dringlichkeitsantrag
    Antrag nach § 3 -> Antrag
    Antrag nach § 3 BV1 (Die Linke) -> Antrag
    Antrag nach § 3 der GeschO des Rates -> Antrag
    Antrag nach § 3 der GeschO des Rates -> Antrag
    Beantwortung e. mündl. Anfrage (Auss.) -> Mitteilung
    Beantwortung einer Anfrage (Ausschuss) -> Mitteilung
    Beantwortung einer Anfrage (BV) -> Mitteilung
    Beantwortung einer Anfrage (Rat) -> Mitteilung
    Beantwortung einer mündl. Anfrage (BV) -> Mitteilung
    Beschlussvorlage -> Beschlussvorlage
    Beschlussvorlage Ausschuss -> Beschlussvorlage
    Beschlussvorlage Bezirksvertretung -> Beschlussvorlage
    Beschlussvorlage Rat / Hauptausschuss -> Beschlussvorlage
    Beschlussvorlage Rat bzw. Hauptausschuss -> Beschlussvorlage
    CDU Anfrage nach § 4 -> Anfrage
    CDU Antrag nach § 5 -> Antrag
    Die Linke. Antrag nach § 3 -> Antrag
    Dringlichkeitsantrag BV6 (CDU) -> Dringlichkeitsantrag
    Dringlichkeitsvorlage -> Dringlichkeitsvorlage
    Dringlichkeitsvorlage Ausschuss -> Dringlichkeitsvorlage
    Dringlichkeitsvorlage Bezirksvertretung -> Dringlichkeitsvorlage
    Dringlichkeitsvorlage BV -> Dringlichkeitsvorlage
    Dringlichkeitsvorlage Hauptauss. /Rat A -> Dringlichkeitsvorlage
    Dringlichkeitsvorlage Hauptausschuss -> Dringlichkeitsvorlage
    Dringlichkeitsvorlage Rat -> Dringlichkeitsvorlage
    FDP Antrag nach § 3 -> Antrag
    Gem. Anfrage nach § 4 (SPD) -> Anfrage
    Gem. Änderungsantrag (SPD) -> Antrag
    Mitteilung Ausschuss -> Mitteilung
    Mitteilung BV -> Mitteilung
    Mitteilung/Beantwortung - Ausschuss -> Mitteilung
    Mitteilung/Beantwortung - BV -> Mitteilung
    Mitteilungsvorlage -> Mitteilung
    Pro Köln Anfrage nach § 4 -> Anfrage
    Pro Köln Antrag nach § 3 -> Antrag
    SPD Anfrage nach § 4 -> Anfrage
    Stellungnahme zu e. Antrag (Ausschuss) -> Mitteilung
    Stellungnahme zu einem Antrag (BV) -> Mitteilung
    Stellungnahme zu einem Antrag (Rat) -> Mitteilung
    Stellungnahme/Beantwortung - Rat -> Mitteilung
    """

    dt = dtype.lower()
    if 'stellungnahme' in dt:
        return 'Mitteilung'
    if 'beantwortung' in dt:
        return 'Mitteilung'
    if 'mitteilung' in dt:
        return 'Mitteilung'
    if 'dringlichkeitsantrag' in dt:
        return 'Dringlichkeitsantrag'
    if 'dringlichkeitsvorlage' in dt:
        return 'Dringlichkeitsvorlage'
    if 'beschlussvorlage' in dt:
        return 'Beschlussvorlage'
    if 'antrag' in dt:
        return 'Antrag'
    if 'anfrage' in dt:
        return 'Anfrage'

    print >> sys.stderr, "Vorlagentyp nicht auflösbar:", dtype
    return ''


def positions_for_streetnames(names):
    """
    Gibt Geo-Koordinaten von Punkten zu einer Straße aus.
    TODO: Auslagern, da bereits in Webapp vorhanden.
    """
    global db
    if names is None or names == []:
        return None
    sql = '''SELECT DISTINCT latitude, longitude
        FROM geo_objects
        LEFT JOIN geo_objects2nodes
            ON geo_objects.id=geo_objects2nodes.object_id
        LEFT JOIN geo_nodes
            ON geo_objects2nodes.node_id=geo_nodes.id
        WHERE name IN(%s) AND latitude is not NULL'''
    namesstrings = []
    for name in names:
        namesstrings.append("'" + name.encode('utf-8') + "'")
    try:
        db.cursor.execute(sql % (", ".join(namesstrings)))
        rows = []
        while (1):
            row = db.cursor.fetchone()
            if row == None:
                break
            rows.append(str(row['latitude']) + ',' + str(row['longitude']))
        return rows
    except MySQLdb.Error, e:
        print >> sys.stderr, ("Fehler in positions_for_streetnames() %d: %s"
                 % (e.args[0], e.args[1]))
        return None


def earliest_document_date(documents):
    """
    Gibt das älteste Dokumenten-Datum zurück
    """
    if len(documents) == 1:
        return documents[0]['date']
    dates = []
    for d in documents:
        if 'date' in d and d['date'] is not None:
            dates.append(d['date'])
    dates = sorted(dates)
    if len(dates) > 0:
        return dates[0]


def calculate_importance(date=None, num_attachments=None,
                         num_attachment_pages=None,
                         num_consultations=None):
    """
    Berechnet die "Wichtigkeit" eines Dokuments
    """
    #print date, num_attachments, num_attachment_pages, num_consultations
    importance = 1.0
    if num_consultations is not None:
        importance *= max(1.0, float(num_consultations) * 20.0)
    if num_attachments is not None:
        importance *= max(1.0, float(num_attachments) * 10.0)
    if num_attachment_pages is not None:
        importance *= max(1.0, float(num_attachment_pages) * 0.2)
    if date is not None:
        diff = (datetime.datetime.now() -
                datetime.datetime.combine(date, datetime.time()))
        if diff.days < 30:
            importance *= 16.0
        if diff.days < 60:
            importance *= 10.0
        if diff.days < 90:
            importance *= 7.0
        if diff.days < 180:
            importance *= 5.0
        if diff.days < 365:
            importance *= 3.0
        if diff.days > (365 * 3):
            importance *= 0.5
    #print "Importance:", importance
    return importance


def import_doc(reference, streets, verbose=False):
    """
    Importiert das Dokument mit der gegebenen Kennung
    """
    global s
    global db
    documents = db.get_documents(reference=reference)
    if verbose:
        print "%d Dokument(e): %s (id=%d)" % (len(documents), documents[0]['title'], documents[0]['id'])
    # Objekte in Beziehung abrufen
    agendaitems = db.get_agendaitems(reference=reference)
    attachments = db.get_attachments(reference=reference)
    attendees = db.get_attendees(reference=reference)
    solr_body = u''
    solr_attachments = {}
    solr_attachment_bodies = {}
    #solr_agendaitem_subjects = {}
    solr_sessions = {}
    solr_committees = {}
    solr_people = {}
    solr_streets = {}
    # Tagesordnungspunkte
    num_consultations = 0
    if agendaitems is not None and len(agendaitems) > 0:
        num_consultations = len(agendaitems)
        for ai in agendaitems:
            if ai['session_id'] is None or ai['session_identifier'] is None:
                continue
            solr_sessions[ai['session_id']] = str(ai['session_id']) + ' ' + ai['session_identifier'].decode('utf-8')
            if ai['committee_id'] is not None:
                solr_committees[ai['committee_id']] = str(ai['committee_id']) + ' ' + ai['committee_name'].decode('utf-8')
                #TODO: Wenn scraper Zuordnung zu Tagesordnungspunkten robust ermittelt:
                # - Betreffzeilen von tagesordnungspunkten mit in Suchtext aufnehmen
                # - Straßennamen in Tagesordnungspunkt-Betreff finden
                # solr_body += " ".join(solr_agendaitem_subjects.values())
    # Anlagen
    num_attachments = 0
    numpages_sum = 0
    if attachments is not None and len(attachments) > 0:
        num_attachments = len(attachments)
        for at in attachments:
            if verbose:
                print "###### Anhang:", at['attachment_role'], at['attachment_filename']
            if at['attachment_content'] is not None:
                clean_text = normalize_text(at['attachment_content'].decode('utf-8'))
                solr_attachment_bodies[int(at['attachment_id'])] = clean_text
                solr_attachments[at['attachment_id']] = str(at['attachment_id']) + ' ' + at['attachment_role'].decode('utf-8')
                # Straßen finden
                matching_streets_attachments = match_streets(streets, clean_text.encode('utf-8'))
                if matching_streets_attachments is not None:
                    for street in matching_streets_attachments:
                        solr_streets[street.decode('utf-8')] = True
            if at['numpages'] is not None:
                numpages_sum += at['numpages']
        solr_body += " ".join(solr_attachment_bodies.values())

    # Verknuepfte Personen
    if attendees is not None:
        for person in attendees:
            if person['person_name'] is None:
                continue
            personstring = str(person['person_id']) + ' ' + person['person_name'].decode('utf-8')
            if person['person_organization'] is not None:
                personstring += ' (' + person['person_organization'].decode('utf-8') + ')'
            solr_people[person['person_id']] = personstring
    datestring = None
    date = earliest_document_date(documents)
    if date is not None:
        datestring = date.strftime('%Y-%m-%dT%H:%M:%SZ')
    importance = calculate_importance(date=date, num_attachments=num_attachments,
                                      num_attachment_pages=numpages_sum,
                                      num_consultations=num_consultations)
    try:
        s.add(reference=reference,
              importance=importance,
              title=documents[0]['title'].decode('utf-8'),
              type=normalize_doctype(documents[0]['type']),
              date=datestring,
              attachment=solr_attachments.values(),
              session=solr_sessions.values(),
              committee=solr_committees.values(),
              street=unique(solr_streets.keys()),
              person=solr_people.values(),
              content=solr_body,
              #location=positions_for_streetnames(unique(solr_streets.keys()))
              )
    except UnicodeDecodeError, err:
        print >> sys.stderr, (
            "UnicodeDecodeError beim Import von request_id", reference)
        print >> sys.stderr, err
        print >> sys.stderr, {'reference:': reference,
                              'title': documents[0]['title'].decode('utf-8'),
                              'date': datestring,
                              'attachment': solr_attachments.values(),
                              'session': solr_sessions.values(),
                              'committee': solr_committees.values(),
                              'street': unique(solr_streets.keys()),
                              'person': solr_people.values(),
                              'content': solr_body,
                              #'location': positions_for_streetnames(unique(solr_streets.keys()))
                              }

if __name__ == '__main__':
    s = solr.SolrConnection(config.SOLR_URL)
    db = DataStore(config.DB_NAME, config.DB_HOST, config.DB_USER, config.DB_PASS)
    parser = OptionParser()
    parser.add_option("-s", "--sample", dest="sample", default=1,
                  help="z.B. die Zahl 10 um nur jedes zehnte Dokument zu importieren. Beschleunigt den Import beim Entwickeln.")
    parser.add_option("-v", "--verbose", dest="verbose", default=False, action="store_true",
                  help="Aktiviert die detailliertere Ausgabe (Dokumententitel etc.).")
    (options, args) = parser.parse_args()
    options.sample = int(options.sample)

    if options.sample != 1:
        print "\nACHTUNG: Es wird nur jedes %d. Dokument importiert.\n" % options.sample

    streets = load_streets(config.STREETS_FILE)

    num_docs = 0

    # Alle Aktenzeichen lesen
    references = db.get_references()
    num_overall = len(references)

    # Bisherige Dokumente aus Solr Löschen.
    # Wird erst ganz am Ende bei commit wirksam.
    s.delete(queries=['reference:*'])

    for reference in references:
        num_docs += 1
        if num_docs % options.sample != 0:
            continue
        print "%d von %d (%.2f%%) - reference: %s" % (num_docs, num_overall, ((float(num_docs) / float(num_overall)) * 100.0), reference)
        import_doc(reference, verbose=options.verbose, streets=streets)

    s.commit(wait_flush=True, wait_searcher=False)
    s.optimize()
    print num_docs, "Dokumente geschrieben"

