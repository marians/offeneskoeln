# encoding: utf-8

"""
Importiert Knoten und Strassen aus der angegebenen OSM-Datei in MongoDB.
Die Datenbank wird vorher geleert!

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

sys.path.append('../../')

import config
from imposm.parser import OSMParser
from pymongo import MongoClient
from bson.son import SON

import pprint


# Wir legen alle nodes in diesem dict ab. Das bedeutet, dass wir
# ausreichend Arbeitsspeicher voraussetzen.
nodes = {}


class NodeCollector(object):
    def coords(self, coords):
        for osmid, lon, lat in coords:
            if osmid not in nodes:
                nodes[osmid] = {
                    'osmid': osmid,
                    'location': [lon, lat]
                }
            nodes[osmid]['lat'] = lat
            nodes[osmid]['lon'] = lat
    #def nodes(self, n):
    #    for osmid, tags, coords in n:
    #        nodes[osmid] = {
    #            'osmid': osmid,
    #            'location': [coords[0], coords[1]],
    #            'tags': tags
    #        }


class StreetCollector(object):
    wanted_nodes = {}
    streets = []
    #street_to_node = []

    def ways(self, ways):
        #global nodes
        for osmid, tags, refs in ways:
            if 'highway' not in tags or 'name' not in tags:
                # Wenn der way keinen "highway" tag hat oder keinen
                # Namen, ist er für uns nicht interessant.
                continue
            street = {
                'osmid': osmid,
                'name': tags['name'],
                'nodes': []
            }
            for ref in refs:
                if ref not in nodes:
                    continue
                self.wanted_nodes[ref] = True
                #self.street_to_node.append((osmid, ref))
                street['nodes'].append(ref)
            self.streets.append(street)

if __name__ == '__main__':

    connection = MongoClient(config.DB_HOST, config.DB_PORT)
    db = connection[config.DB_NAME]
    db.locations.remove()
    db.locations.ensure_index('osmid', unique=True)
    db.locations.ensure_index('name')
    db.locations.ensure_index([('nodes.location', '2dsphere')])

    print "Sammle nodes..."
    nodecollector = NodeCollector()
    p = OSMParser(concurrency=2, coords_callback=nodecollector.coords)
    p.parse(sys.argv[1])

    print "Sammle Straßen..."
    streetcollector = StreetCollector()
    p = OSMParser(concurrency=2, ways_callback=streetcollector.ways)
    p.parse(sys.argv[1])

    # Iteriere über alle gesammelten nodes und finde die,
    # welche von anderen Objekten referenziert werden.
    wanted_nodes = {}
    non_existing_nodes = 0
    for ref in streetcollector.wanted_nodes.keys():
        if ref in nodes:
            wanted_nodes[ref] = nodes[ref]
        else:
            non_existing_nodes += 1

    # reduziere das nodes dict auf das wesentliche
    wanted_nodes.values()

    for street in streetcollector.streets:
        for n in range(len(street['nodes'])):
            street['nodes'][n] = {
                'osmid': street['nodes'][n],
                'location': SON([
                    ('type', 'Point'),
                    ('coordinates', wanted_nodes[street['nodes'][n]]['location'])
                ])
            }
        db.locations.save(street)
