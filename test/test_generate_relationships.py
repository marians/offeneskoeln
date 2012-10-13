#!/usr/bin/python
# encoding: utf-8

"""
Testscript für das date_range Modul

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
import generate_relationships as gr


class TestGenerateRelationships(unittest.TestCase):

    def setup(self):
        pass

    def test_regex1(self):
        self.assertEqual(
            gr.get_references_in_text('Antrag AN/1234/2011 blah'),
            ['AN/1234/2011'])

    def test_regex2(self):
        self.assertEqual(
            gr.get_references_in_text('Vorlage 1234/2011 blah'),
            ['1234/2011'])

    def test_regex3(self):
        self.assertEqual(
            gr.get_references_in_text('Vorlage 1234/2011/01 blah'),
            ['1234/2011/01'])

    def test_regex4(self):
        self.assertEqual(
            gr.get_references_in_text('Antrag AN 1234/2011 blah'),
            ['AN 1234/2011'])

    def test_regex5(self):
        self.assertEqual(
            gr.get_references_in_text('Antrag AN/1234/2011 und Vorlage 4545/1234 blah'),
            ['AN/1234/2011', '4545/1234'])

    def test_regex6(self):
        self.assertEqual(
            gr.get_references_in_text('Antrag AN/1234/2011 und Vorlage 1234/2011 blah'),
            ['AN/1234/2011', '1234/2011'])


if __name__ == '__main__':
    unittest.main()
