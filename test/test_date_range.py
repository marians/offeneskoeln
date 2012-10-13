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
import date_range
import datetime


class TestDaterange(unittest.TestCase):
    """
    Unit tests für die webapp
    """

    def setup(self):
        pass

    def test_string1(self):
        d = (datetime.date(year=2012, month=1, day=1),
             datetime.date(year=2012, month=12, day=31))
        self.assertEqual(date_range.to_dates('2012'), d)

    def test_string2(self):
        d = (datetime.date(year=2012, month=1, day=1),
             datetime.date(year=2012, month=1, day=31))
        self.assertEqual(date_range.to_dates('201201'), d)

    def test_string3(self):
        d = (datetime.date(year=2012, month=10, day=1),
             datetime.date(year=2012, month=10, day=1))
        self.assertEqual(date_range.to_dates('20121001'), d)

    def test_string4(self):
        d = (datetime.date(year=2011, month=1, day=1),
             datetime.date(year=2011, month=12, day=31))
        self.assertEqual(date_range.to_dates('2011-2011'), d)

    def test_string5(self):
        d = (datetime.date(year=2011, month=1, day=1),
             datetime.date(year=2012, month=12, day=31))
        self.assertEqual(date_range.to_dates('2011-2012'), d)

    def test_string6(self):
        d = (datetime.date(year=2011, month=4, day=1),
             datetime.date(year=2012, month=12, day=31))
        self.assertEqual(date_range.to_dates('201104-2012'), d)

    def test_string7(self):
        d = (datetime.date(year=2011, month=4, day=1),
             datetime.date(year=2012, month=3, day=31))
        self.assertEqual(date_range.to_dates('201104-201203'), d)

    def test_string8(self):
        d = (datetime.date(year=2011, month=4, day=8),
             datetime.date(year=2011, month=12, day=31))
        self.assertEqual(date_range.to_dates('20110408-2011'), d)

    def test_string9(self):
        d = (datetime.date(year=2011, month=1, day=1),
             datetime.date(year=9999, month=12, day=31))
        self.assertEqual(date_range.to_dates('2011-'), d)

    def test_string10(self):
        d = (datetime.date(year=2011, month=4, day=1),
             datetime.date(year=9999, month=12, day=31))
        self.assertEqual(date_range.to_dates('201104-'), d)

    def test_string11(self):
        d = (datetime.date(year=2011, month=4, day=8),
             datetime.date(year=9999, month=12, day=31))
        self.assertEqual(date_range.to_dates('20110408-'), d)

    def test_string12(self):
        d = (datetime.date(year=1, month=1, day=1),
             datetime.date(year=2011, month=12, day=31))
        self.assertEqual(date_range.to_dates('-2011'), d)

    def test_string13(self):
        d = (datetime.date(year=1, month=1, day=1),
             datetime.date(year=2011, month=4, day=30))
        self.assertEqual(date_range.to_dates('-201104'), d)

    def test_string14(self):
        d = (datetime.date(year=1, month=1, day=1),
             datetime.date(year=2011, month=4, day=8))
        self.assertEqual(date_range.to_dates('-20110408'), d)

    def test_string15(self):
        d = (datetime.date(year=2009, month=2, day=1),
             datetime.date(year=2009, month=2, day=28))
        self.assertEqual(date_range.to_dates('200902'), d)

    def test_string16(self):
        d = (datetime.date(year=2010, month=2, day=1),
             datetime.date(year=2010, month=2, day=28))
        self.assertEqual(date_range.to_dates('201002'), d)

    def test_string17(self):
        d = (datetime.date(year=2011, month=2, day=1),
             datetime.date(year=2011, month=2, day=28))
        self.assertEqual(date_range.to_dates('201102'), d)

    def test_string18(self):
        d = (datetime.date(year=2012, month=2, day=1),
             datetime.date(year=2012, month=2, day=29))
        self.assertEqual(date_range.to_dates('201202'), d)

    def test_string19(self):
        d = (datetime.date(year=2013, month=2, day=1),
             datetime.date(year=2013, month=2, day=28))
        self.assertEqual(date_range.to_dates('201302'), d)

if __name__ == '__main__':
    unittest.main()
