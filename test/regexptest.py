#!/usr/bin/python
# encoding: utf-8

import re

fulltext = """
blabla
bla

"Lärmschutz Freizeitzentrum Kemnade und Zeltfestival Ruhr"
- Anfrage der Fraktion "Die Grünen im Rat" Vorlage: 20130337
blablabla

3

"""



pattern = '\"L\ärmschutz\\sFreizeitzentrum\\sKemnade\\sund\\sZeltfestival\\sRuhr\"\\s\-\\sAnfrage\\sder\\sFraktion\\s\"Die\\sGr\ünen\\sim\\sRat\"(.*?)\n\n\d'
result = re.search(pattern, fulltext, flags=re.DOTALL|re.UNICODE)
print result.group(1)