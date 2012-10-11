#!/usr/bin/env python
# encoding: utf-8

"""
Importiert Knoten und Strassen aus der angegebenen OSM-Datei in MySQL.
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
from imposm.parser import OSMParser
import MySQLdb
import config


# Wir legen alle nodes in diesem dict ab. Das bedeutet, dass wir
# Arbeitsspeicher brauchen und dass dieses Script nicht unbedingt
# für größere Räume als Köln geeignet ist.
nodes = {}


class NodeCollector(object):
    def coords(self, coords):
        for osmid, lon, lat in coords:
            nodes[osmid] = (osmid, lat, lon)


class StreetCollector(object):
    wanted_nodes = {}
    streets = []
    street_to_node = []

    def ways(self, ways):
        #global nodes
        for osmid, tags, refs in ways:
            if 'highway' not in tags or 'name' not in tags:
                # Wenn der way keinen "highway" tag hat oder keinen
                # Namen, ist er für uns nicht interessant.
                continue
            self.streets.append((osmid, tags['name'].encode('utf-8'), 'highway', tags['highway'].encode('utf-8')))
            for ref in refs:
                if ref not in nodes:
                    continue
                self.wanted_nodes[ref] = True
                self.street_to_node.append((osmid, ref))

if __name__ == '__main__':
    try:
        conn = MySQLdb.connect(host=config.DB_HOST, user=config.DB_USER, passwd=config.DB_PASS, db=config.DB_NAME)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SET NAMES 'utf8'")
        cursor.execute("SET CHARACTER SET 'utf8'")
    except MySQLdb.Error, e:
        print >> sys.stderr, "Error %d: %s" % (e.args[0], e.args[1])
        sys.exit(1)

    print "Sammle nodes..."
    nodecollector = NodeCollector()
    p = OSMParser(concurrency=2, coords_callback=nodecollector.coords)
    p.parse(sys.argv[1])

    print "Sammle Straßen..."
    streetcollector = StreetCollector()
    p = OSMParser(concurrency=2, ways_callback=streetcollector.ways)
    p.parse(sys.argv[1])

    # iterate through collected nodes to find the requires ones
    wanted_nodes = {}
    non_existing_nodes = 0
    for ref in streetcollector.wanted_nodes.keys():
        if ref in nodes:
            wanted_nodes[ref] = nodes[ref]
        else:
            non_existing_nodes += 1

    nodes = wanted_nodes.values()
    cursor.execute('DELETE FROM geo_nodes')
    cursor.executemany("INSERT INTO geo_nodes (id, latitude, longitude) VALUES (%s, %s, %s)", nodes)

    cursor.execute('DELETE FROM geo_objects')
    cursor.executemany("INSERT INTO geo_objects (id, name, type, subtype) VALUES (%s, %s, %s, %s)", streetcollector.streets)

    cursor.execute('DELETE FROM geo_objects2nodes')
    cursor.executemany("INSERT IGNORE INTO geo_objects2nodes (object_id, node_id) VALUES (%s, %s)", streetcollector.street_to_node)

    print ""
    print non_existing_nodes, "referenzierte nodes wurden nicht gefunden."
    print len(nodes), "nodes importiert."
    print len(streetcollector.streets), "Straßen (ways) importiert."
    print len(streetcollector.street_to_node), "node-way-Beziehungen importiert."
