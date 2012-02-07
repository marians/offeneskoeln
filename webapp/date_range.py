#!/usr/bin/python
# encoding: utf-8

"""
    Utility für Zeichenketten zur Angabe von Datumszeiträumen
    
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

import datetime
from calendar import monthrange

"""
    This function takes a date URL parameter in various string formats
    and converts it to a normalized and validated date range. A list
    with two elements is returned, lower and upper date boundary.
    
    Valid inputs are, for example:
    2012              => Jan 1 20012 - Dec 31 2012 (whole year)
    201201            => Jan 1 2012  - Jan 31 2012 (whole month)
    2012101           => Jan 1 2012 - Jan 1 2012   (whole day)
    2011-2011         => same as "2011", which means whole year 2012
    2011-2012         => Jan 1 2011 - Dec 31 2012  (two years)
    201104-2012       => Apr 1 2011 - Dec 31 2012
    201104-201203     => Apr 1 2011 - March 31 2012
    20110408-2011     => Apr 8 2011 - Dec 31 2011
    20110408-201105   => Apr 8 2011 - May 31 2011
    20110408-20110507 => Apr 8 2011 - May 07 2011
    2011-             => Jan 1 2012 - Dec 31 9999 (unlimited)
    201104-           => Apr 1 2011 - Dec 31 9999 (unlimited)
    20110408-         => Apr 8 2011 - Dec 31 9999 (unlimited)
    -2011             Jan 1 0000 - Dez 31 2011
    -201104           Jan 1 0000 - Apr 30, 2011
    -20110408         Jan 1 0000 - Apr 8, 2011
"""
def range_string_to_dates(param):
    pos = param.find('-')
    lower, upper = (None, None)
    if pos == -1:
        # no seperator given
        lower, upper = (param, param)
    else:
        lower, upper = param.split('-')
    ret = (expand_date_param(lower, 'lower'), expand_date_param(upper, 'upper'))
    return ret

"""
    Expands an (possibly) incomplete date string to either the lowest
    or highest possible contained date and returns
    datetime.date for that string.
    
    0753 (lowest) => 0753-01-01
    2012 (highest) => 2012-12-31
    2012 (lowest) => 2012-01-01
    201208 (highest) => 2012-08-31
    etc.
"""
def expand_date_param(param, lower_upper):
    year = 0
    month = 0
    day = 0
    if len(param) == 0:
        if lower_upper == 'lower':
            year = datetime.MINYEAR
            month = 1
            day = 1
        else:
            year = datetime.MAXYEAR
            month = 12
            day = 31
    elif len(param) == 4:
        year = int(param)
        if lower_upper == 'lower':
            month = 1
            day = 1
        else:
            month = 12
            day = 31
    elif len(param) == 6:
        year = int(param[0:4])
        month = int(param[4:6])
        if lower_upper == 'lower':
            day = 1
        else:
            (firstday, dayspermonth) = monthrange(year, month)
            day = dayspermonth
    elif len(param) == 8:
        year = int(param[0:4])
        month = int(param[4:6])
        day = int(param[6:8])
    else:
        # wrong input length
        return None
    # force numbers into valid ranges
    year = min(datetime.MAXYEAR, max(datetime.MINYEAR, year))
    month = min(12, max(1, month))
    (firstday, dayspermonth) = monthrange(year, month)
    day = min(dayspermonth, max(1, day))
    return datetime.date(year=year, month=month, day=day)
    
    
    
def test():
    print process_date_range_param('2012')
    print process_date_range_param('201201')
    print process_date_range_param('20121001')
    print process_date_range_param('2011-2011')
    print process_date_range_param('2011-2012')
    print process_date_range_param('201104-2012')
    print process_date_range_param('201104-201203')
    print process_date_range_param('20110408-2011')
    print process_date_range_param('2011-')
    print process_date_range_param('201104-')
    print process_date_range_param('20110408-')
    print process_date_range_param('-2011')
    print process_date_range_param('-201104')
    print process_date_range_param('-20110408')
    print process_date_range_param('200902')
    print process_date_range_param('201002')
    print process_date_range_param('201102')
    print process_date_range_param('201202')
    print process_date_range_param('201302')

