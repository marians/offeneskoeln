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
import os
import MySQLdb

class DataStore:
    def __init__(self, dbname, host='localhost', user='root', password=''):
        try:
            self.conn = MySQLdb.connect (host = host, user = user, passwd = password, db = dbname)
            self.cursor = self.conn.cursor(MySQLdb.cursors.DictCursor)
            self.cursor.execute("SET NAMES 'utf8'")
            self.cursor.execute("SET CHARACTER SET 'utf8'")
        except MySQLdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit (1)
    def execute(self, sql, values):
        self.cursor.execute(sql, values)
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
            data = [ data ]
        for thedict in data:
            values = []
            sql = 'INSERT IGNORE INTO ' + table +' ('+ ', '.join(thedict.keys()) +')'
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
    
    def get_submissions(self):
        return self.get_rows('SELECT * FROM submissions ORDER BY submission_date DESC')
    
    def get_requests(self):
        return self.get_rows('SELECT * FROM requests ORDER BY request_date DESC')

    def get_agendaitems_by_submission_id(self, submission_id):
        return self.get_rows('''SELECT * FROM agendaitems2submissions 
            LEFT JOIN agendaitems ON agendaitems2submissions.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN committees ON committees.committee_id=sessions.committee_id
            WHERE submission_id=%d
            ORDER BY session_date, session_time_start''' % submission_id)
    
    def get_agendaitems_by_request_id(self, request_id):
        return self.get_rows('''SELECT * FROM agendaitems2requests 
            LEFT JOIN agendaitems ON agendaitems2requests.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN committees ON committees.committee_id=sessions.committee_id
            WHERE request_id=%d
            ORDER BY session_date, session_time_start''' % request_id)

    def get_attachments_by_submission_id(self, submission_id):
        return self.get_rows('''SELECT * FROM submissions2attachments 
            LEFT JOIN attachments ON submissions2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN agendaitems2attachments ON agendaitems2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN agendaitems ON agendaitems.agendaitem_id=agendaitems2attachments.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN committees ON committees.committee_id=sessions.committee_id
            WHERE submission_id=%d
            ORDER BY session_date, session_time_start''' % submission_id)
            
    def get_attachments_by_request_id(self, request_id):
        return self.get_rows('''SELECT * FROM requests2attachments 
            LEFT JOIN attachments ON requests2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN agendaitems2attachments ON agendaitems2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN agendaitems ON agendaitems.agendaitem_id=agendaitems2attachments.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN committees ON committees.committee_id=sessions.committee_id
            WHERE request_id=%d
            ORDER BY session_date, session_time_start''' % request_id)

    def get_attending_people_by_submission_id(self, submission_id):
        return self.get_rows('''SELECT DISTINCT agendaitems2submissions.submission_id, people.person_id, person_name, person_organization 
            FROM agendaitems2submissions 
            LEFT JOIN agendaitems ON agendaitems2submissions.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN attendance ON agendaitems.session_id=attendance.session_id
            LEFT JOIN people ON attendance.person_id=people.person_id
            WHERE submission_id=%d''' % submission_id)

    def get_attending_people_by_request_id(self, request_id):
        return self.get_rows('''SELECT DISTINCT agendaitems2requests.request_id, people.person_id, person_name, person_organization 
            FROM agendaitems2requests 
            LEFT JOIN agendaitems ON agendaitems2requests.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions ON sessions.session_id=agendaitems.session_id
            LEFT JOIN attendance ON agendaitems.session_id=attendance.session_id
            LEFT JOIN people ON attendance.person_id=people.person_id
            WHERE request_id=%d''' % request_id)