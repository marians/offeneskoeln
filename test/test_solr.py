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
import config
import solr


class TestSolr(unittest.TestCase):
    """
    Unit tests für den Solr-Zugriff
    """

    def setUp(self):
        self.connection = solr.SolrConnection(config.SOLR_URL)

    def test_query(self):
        response = self.connection.query('*:*')
        self.assertNotEqual(response, None)
        self.assertTrue(len(response.results) > 0)

    def test_add_incomplete(self):
        """Neues Dokument mit fehlenden Pflichtfeldern (importance)"""
        self.assertRaises(solr.SolrException, self.connection.add,
            reference="blahblub")
        self.connection.commit()

    def test_add_ascii1(self):
        """Versuch 1, Dokument mit Nicht-ASCII-Zeichen anzulegen"""
        self.assertRaises(UnicodeDecodeError, self.connection.add,
            title="Schließung Köln")

    def test_add_ascii2(self):
        """Versuch 2, Dokument mit Nicht-ASCII-Zeichen anzulegen"""
        doc = {
            'reference': "nonasciitest",
            'importance': 1.0,
            'title': 'Schließung Köln'
        }
        self.assertRaises(solr.SolrException, self.connection.add, doc)
        self.connection.commit()

    def test_add(self):
        """Neues Dokument anlegen"""
        self.connection.add(reference="abcde12345",
            importance=1.0, title=u'Schlie\xdfung K\xf6ln')
        self.connection.commit()
        response = self.connection.query('reference:abcde12345')
        self.assertNotEqual(response, None)
        self.assertEqual(len(response.results), 1)

    def test_charset(self):
        """Zeichensatz-Test"""
        response = self.connection.query('reference:abcde12345')
        doc = response.results[0]
        self.assertEqual(doc['title'], u'Schlie\xdfung K\xf6ln')

    def test_delete(self):
        """Dokument löschen"""
        self.connection.delete("abcde12345")
        self.connection.commit()
        response = self.connection.query('reference:abcde12345')
        self.assertNotEqual(response, None)
        self.assertEqual(len(response.results), 0)


if __name__ == '__main__':
    unittest.main()
