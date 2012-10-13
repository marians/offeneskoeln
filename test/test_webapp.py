#!/usr/bin/python
# encoding: utf-8

"""
Testscript für die Web-Applikation

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

import unittest
import dispatch


class TestWebapp(unittest.TestCase):
    """
    Unit tests für die webapp
    """

    def setup(self):
        pass

    def test_valid_document_reference(self):
        self.assertTrue(dispatch.valid_document_reference('AN/0123/5678'))
        self.assertTrue(dispatch.valid_document_reference('AN/0123/5678/2'))
        self.assertTrue(dispatch.valid_document_reference('AN/0123/5678/89'))
        self.assertTrue(dispatch.valid_document_reference('7935/2012'))
        self.assertFalse(dispatch.valid_document_reference('567686'))
        self.assertFalse(dispatch.valid_document_reference('567/0686'))
        self.assertFalse(dispatch.valid_document_reference('5676/862'))
        self.assertFalse(dispatch.valid_document_reference('A/5676/8862'))

    #def test_placefinder_geocode_1(self):
    #    address = dispatch.placefinder_geocode(u'Aachenerstraße')
    #    # TODO: echtes Result-Objekt eintragen
    #    result = {}
    #    self.assertEqual(address, result)

    def test_get_documents_1(self):
        """Einfacher Abruf eines Dokuments ohne weitere Details"""
        docs = dispatch.get_documents(['2021/2011'])
        self.assertEqual(len(docs), 1)
        self.assertEqual(len(docs['2021/2011']), 1)
        self.assertNotEqual(docs['2021/2011'][0]['url'], None)
        self.assertEqual(docs['2021/2011'][0]['title'],
            u'Schließung Wachsfabrik Köln AN/0856/2011')
        self.assertEqual(docs['2021/2011'][0]['original_url'],
            'http://ratsinformation.stadt-koeln.de/ag0050.asp?__kagnr=28125')
        self.assertEqual(docs['2021/2011'][0]['date'], '2011-05-18')
        self.assertEqual(docs['2021/2011'][0]['reference'], u'2021/2011')
        self.assertEqual(docs['2021/2011'][0]['type'],
            u'Mitteilung/Beantwortung - BV')

    def test_get_documents_2(self):
        """Dokumentenabruf mit zusaetzlichen Details"""
        docs = dispatch.get_documents(references=['AN/0438/2010'],
                get_attachments=True, get_thumbnails=True,
                get_consultations=True)
        self.assertTrue(len(docs) == 1)
        con = docs['AN/0438/2010'][0]['consultations']
        att = docs['AN/0438/2010'][0]['attachments']
        thumb = att[0]['thumbnails']
        # testing consultation
        self.assertNotEqual(con[0]['agendaitem_title'], None)
        self.assertNotEqual(con[0]['committee_id'], None)
        self.assertNotEqual(con[0]['agendaitem_number'], None)
        self.assertNotEqual(con[0]['date'], None)
        self.assertNotEqual(con[0]['committee_name'], None)
        self.assertNotEqual(con[0]['session_description'], None)
        self.assertIn('agendaitem_result', con[0])
        # test attachments
        self.assertNotEqual(att)
        self.assertGreater(len(att), 0)
        self.assertIn('last_modified', att[0])
        self.assertNotEqual(att[0]['numpages'], None)
        self.assertNotEqual(att[0]['url'], None)
        self.assertNotEqual(att[0]['filename'], None)
        self.assertNotEqual(att[0]['content'], None)
        self.assertNotEqual(att[0]['type'], None)
        self.assertNotEqual(att[0]['id'], None)
        self.assertNotEqual(att[0]['size'], None)
        self.assertIsNone(att[0]['exclusion'])
        # test attachment thumbnails
        self.assertIn('thumbnails', att[0])
        self.assertNotEqual(thumb, None)
        self.assertGreater(len(thumb), 0)
        self.assertNotEqual(thumb[0]['url'], None)
        self.assertNotEqual(thumb[0]['width'], None)
        self.assertNotEqual(thumb[0]['height'], None)
        self.assertNotEqual(thumb[0]['page'], None)

    def test_solr_query_1(self):
        """Einfache Solr-Suche"""
        q = dispatch.solr_query(q='reference:"AN/0438/2010"')
        self.assertEqual(type(q), dict)
        self.assertIn('status', q)
        self.assertEqual(q['status'], 0)

    def test_solr_query_2(self):
        q = dispatch.solr_query(q='straßenverkehr ampel', docs=10)
        self.assertEqual(type(q), dict)
        self.assertIn('status', q)
        self.assertEqual(q['status'], 0)

if __name__ == '__main__':
    unittest.main()
