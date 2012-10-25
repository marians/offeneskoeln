# encoding: utf-8

"""
Das Script gibt aus, wieviele Nutzer (=Sessiosn) zum aktuellen Zeitpunkt
auf der Web-Plattform aktiv sind. Als aktiv gelten Sessions, die bis zu
fünf Minuten alt sind.

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

import MySQLdb
import sys
import config

if __name__ == '__main__':
    conn = MySQLdb.connect(host=config.DB_HOST, user=config.DB_USER,
        passwd=config.DB_PASS, db=config.DB_NAME)
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute("""SELECT NOW() AS now, COUNT(*) AS num
            FROM webapp_sessiondata
            WHERE atime >= (NOW() - INTERVAL 5 MINUTE)""")
        rows = []
        row = cursor.fetchone()
        print "%s   %d" % (row['now'], int(row['num']))
    except MySQLdb.Error, e:
        sys.stderr.write(("Error %d: %s" % (e.args[0], e.args[1])) + "\n")
