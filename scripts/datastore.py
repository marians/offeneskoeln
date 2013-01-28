#!/usr/bin/env python
# encoding: utf-8

"""
Hilfestellung beim Datenbank-Zugriff

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
import MySQLdb
from MySQLdb import MySQLError


class DataStore:
    def __init__(self, dbname, host='localhost', user='root', password=''):
        try:
            self.conn = MySQLdb.connect(host=host, user=user, passwd=password, db=dbname)
            self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
            self.cursor.execute("SET NAMES 'utf8'")
            self.cursor.execute("SET CHARACTER SET utf8")
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)

    def execute(self, sql, values):
        try:
            self.cursor.execute(sql, values)
        except MySQLError, e:
            #print >> sys.stderr, "Error %d: %s" % (e.args[0], e.args[1])
            #print >> sys.stderr, "Last SQL statement:", sql, values
            raise e

    def get_rows(self, sql):
        try:
            self.cursor.execute(sql)
            rows = []
            while (1):
                row = self.cursor.fetchone()
                if row == None:
                    break
                rows.append(row)
            return rows
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])

    def save_rows(self, table, data, unique_keys):
        if isinstance(data, list):
            pass
        else:
            data = [data]
        for thedict in data:
            values = []
            sql = 'INSERT IGNORE INTO ' + table + ' (' + ', '.join(thedict.keys()) + ')'
            sql2 = ' VALUES ('
            placeholders = []
            for el in thedict.keys():
                placeholders.append("%s")
                if thedict[el] is None:
                    values.append(thedict[el])
                elif isinstance(thedict[el], int) or isinstance(thedict[el], long):
                    values.append(thedict[el])
                else:
                    values.append(thedict[el].encode('utf-8'))
            sql2 += ", ".join(placeholders) + ')'
            sql += sql2
            if unique_keys is not None and unique_keys != []:
                sql3 = ' ON DUPLICATE KEY UPDATE '
                updates = []
                for el in thedict.keys():
                    if el not in unique_keys:
                        updates.append(el + "=%s")
                        if thedict[el] is None:
                            values.append(thedict[el])
                        elif isinstance(thedict[el], int) or isinstance(thedict[el], long):
                            values.append(thedict[el])
                        else:
                            values.append(thedict[el].encode('utf-8'))
                if len(updates) > 0:
                    sql3 += ", ".join(updates)
                    sql += sql3
            #print sql
            self.cursor.execute(sql, values)

    def get_references(self):
        """
        Gibt die Kennungen (z.B. "AN/0123/2011") aller Dokumente
        der Datenbank zurück.
        """
        result = {}
        rows = self.get_rows('''SELECT DISTINCT submission_identifier AS reference
            FROM submissions
            WHERE submission_identifier IS NOT NULL''')
        for row in rows:
            result[row['reference']] = True
        rows = self.get_rows('''SELECT DISTINCT request_identifier AS reference
            FROM requests
            WHERE request_identifier IS NOT NULL''')
        for row in rows:
            result[row['reference']] = True
        return result.keys()

    def get_submissions(self):
        return self.get_rows('SELECT * FROM submissions ORDER BY submission_date DESC')

    def get_requests(self):
        return self.get_rows('SELECT * FROM requests ORDER BY request_date DESC')

    def get_documents(self, reference):
        submissions = self.get_rows("""SELECT submission_subject AS title, submission_identifier AS reference,
            submission_date AS date, submission_id AS id, submission_type AS type
            FROM submissions
            WHERE submission_identifier='%s'""" % reference)
        requests = self.get_rows("""SELECT request_subject AS title, request_identifier AS reference,
            committees.committee_id, committee_title AS committee_name, request_date AS date, 'Antrag' AS type, request_id AS id
            FROM requests
            LEFT JOIN committees ON requests.committee_id=committees.committee_id
            WHERE request_identifier='%s'""" % reference)
        docs = []
        for doc in submissions:
            docs.append(doc)
        for doc in requests:
            docs.append(doc)
        return docs

    def get_agendaitems(self, reference):
        """
        Gibt alle Tagesordnungspunkte (agendaitems) zu einer Kennung (z.B. AN/0123/2011) zurück
        """
        requests = self.get_rows("""SELECT DISTINCT agendaitems.agendaitem_id, agendaitems.agendaitem_identifier,
            agendaitems.agendaitem_subject, agendaitems.agendaitem_result, sessions.session_id, sessions.session_identifier,
            sessions.session_date, sessions.session_title, sessions.session_description, sessions.committee_id,
            committees.committee_title AS committee_name FROM requests
            LEFT JOIN agendaitems2requests ON requests.request_id=agendaitems2requests.request_id
            LEFT JOIN agendaitems ON agendaitems2requests.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN committees ON committees.committee_id=sessions.committee_id
            WHERE request_identifier='%s'
            ORDER BY session_date, session_time_start""" % reference)
        submissions = self.get_rows("""SELECT DISTINCT agendaitems.agendaitem_id, agendaitems.agendaitem_identifier,
            agendaitems.agendaitem_subject, agendaitems.agendaitem_result, sessions.session_id, sessions.session_identifier,
            sessions.session_date, sessions.session_title, sessions.session_description, sessions.committee_id,
            committees.committee_title AS committee_name FROM submissions
            LEFT JOIN agendaitems2submissions ON submissions.submission_id=agendaitems2submissions.submission_id
            LEFT JOIN agendaitems ON agendaitems2submissions.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN committees ON committees.committee_id=sessions.committee_id
            WHERE submission_identifier='%s'
            ORDER BY session_date, session_time_start""" % reference)
        agendaitems = []
        if requests is not None:
            for e in requests:
                agendaitems.append(e)
        if submissions is not None:
            for e in submissions:
                agendaitems.append(e)
        return agendaitems

    def get_attachments(self, reference):
        att1 = self.get_rows("""SELECT DISTINCT attachments.*, submissions2attachments.attachment_role,
            (MAX(attachment_thumbnails.page)+1) AS numpages FROM submissions
            LEFT JOIN submissions2attachments ON submissions.submission_id=submissions2attachments.submission_id
            LEFT JOIN attachments ON submissions2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN agendaitems2attachments ON agendaitems2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN attachment_thumbnails ON attachments.attachment_id=attachment_thumbnails.attachment_id
            WHERE submission_identifier='%s'
            GROUP BY attachments.attachment_id""" % reference)
        att2 = self.get_rows("""SELECT DISTINCT attachments.*, requests2attachments.attachment_role,
            (MAX(attachment_thumbnails.page)+1) AS numpages FROM requests
            LEFT JOIN requests2attachments ON requests.request_id=requests2attachments.request_id
            LEFT JOIN attachments ON requests2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN agendaitems2attachments ON agendaitems2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN attachment_thumbnails ON attachments.attachment_id=attachment_thumbnails.attachment_id
            WHERE request_identifier='%s'
            GROUP BY attachments.attachment_id""" % reference)
        attachments = []
        if att1 is not None:
            for e in att1:
                attachments.append(e)
        if att2 is not None:
            for e in att2:
                attachments.append(e)
        return attachments

    def get_attendees(self, reference):
        att1 = self.get_rows("""SELECT DISTINCT people.person_id, person_name, person_organization
            FROM submissions
            LEFT JOIN agendaitems2submissions ON submissions.submission_id=agendaitems2submissions.submission_id
            LEFT JOIN agendaitems ON agendaitems2submissions.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN attendance ON agendaitems.session_id=attendance.session_id
            LEFT JOIN people ON attendance.person_id=people.person_id
            WHERE submission_identifier='%s'""" % reference)
        att2 = self.get_rows("""SELECT DISTINCT people.person_id, person_name, person_organization
            FROM requests
            LEFT JOIN agendaitems2requests ON requests.request_id=agendaitems2requests.request_id
            LEFT JOIN agendaitems ON agendaitems2requests.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN attendance ON agendaitems.session_id=attendance.session_id
            LEFT JOIN people ON attendance.person_id=people.person_id
            WHERE request_identifier='%s'""" % reference)
        attendees = []
        if att1 is not None:
            for e in att1:
                attendees.append(e)
        if att2 is not None:
            for e in att2:
                attendees.append(e)
        return attendees
