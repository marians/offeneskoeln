#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
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

import config
import web
import os
import json
import solr
import urllib
import urllib2
from email.utils import formatdate
import datetime
import time
import re
import math
import date_range
import sys


urls = (
    '/links/', 'Links',
    '/daten/', 'Daten',
    '/kontakt/', 'Kontakt',
    '/feedback/', 'Feedback',
    '/disclaimer/', 'Disclaimer',
    '/ueber/', 'Ueber',
    '/dokumente/([A-Z0-9-]+)/', 'DokumentDetailseite',
    '/dokumente/', 'DokumentListe',
    '/suche/', 'Suche',
    '/api/', 'ApiPage',
    '/api/documents', 'ApiDocuments',
    '/api/streets', 'ApiStreets',
    '/api/locations', 'ApiLocations',
    '/api/session', 'ApiSession',
    '/api/terms', 'ApiTerms',
    '/api/proxy/geocode', 'ApiGeocode',
    '/', 'Index')

# Konstanten

SAME_ATTACHMENT = 'same_attachment'

#############     Seiten    ################


class Index:
    def GET(self):
        return render.index()

    def POST(self):
        raise web.seeother('/')


class Links:
    def GET(self):
        return render.links()


class Kontakt:
    def GET(self):
        return render.kontakt()


class Feedback:
    def GET(self):
        return render.feedback()


class Disclaimer:
    def GET(self):
        return render.disclaimer()


class Ueber:
    def GET(self):
        return render.ueber()


class Daten:
    def GET(self):
        filelist = []
        path = config.BASE_PATH + os.sep + 'daten'
        for filename in os.listdir(path):
            filepath = path + os.sep + filename
            stat = os.lstat(filepath)
            if os.path.isfile(filepath) or os.path.islink(filepath):
                filelist.append({
                    'name': filename,
                    'size': "%d" % byte_to_mb(stat.st_size),
                })
        return render.daten(filelist)


class DokumentDetailseite:
    def GET(self, reference):
        real_reference = reference.strip().replace('-', '/')
        print real_reference
        if valid_document_reference(real_reference):
            return render.dokument_detailseite(real_reference)
        else:
            raise web.notfound()


class DokumentListe:
    def GET(self):
        """
        Gibt eine sehr simple Liste aller Dokumente mit Links zur
        Detailseite aus.
        """
        documents = []
        result = config.DB.select('requests',
            what='DISTINCT request_identifier AS identifier')
        if len(result) > 0:
            for row in result:
                row['identifier'] = row['identifier'].replace('/', '-')
                documents.append(row)
        result = config.DB.select('submissions',
            what='DISTINCT submission_identifier AS identifier')
        if len(result) > 0:
            for row in result:
                row['identifier'] = row['identifier'].replace('/', '-')
                documents.append(row)
        headers(cache_hours=24)
        return render.dokument_liste(documents)


class Suche:
    def GET(self):
        """
        q: Suchanfrage, nutzer-formuliert
        fq: Filter query (Lucene Syntax)
        sort: Sortierung, z.B. "id asc"
        start: Offset im Suchergebnis
        num: Anzahl der Treffer pro Seite
        date: Datumsbereich als String
        """
        url_params = web.input(q='', fq='', sort='', start='0',
                               num='10', date='')
        url_params.start = max(0, int(url_params.start.strip()))
        url_params.num = min(100, max(10, int(url_params.num.strip())))
        url_params.q = url_params.q.strip()
        url_params.fq = url_params.fq.strip()
        url_params.sort = url_params.sort.strip()
        url_params.date = url_params.date.strip()
        search_settings = {}
        search_settings['q'] = url_params.q
        search_settings['fq'] = url_params.fq
        search_settings['sort'] = url_params.sort
        search_settings['start'] = url_params.start
        search_settings['num'] = url_params.num
        search_settings['date'] = url_params.date
        headers(cache_hours=24)
        return render.suche(search_settings)


class ApiPage:
    def GET(self):
        headers(cache_hours=24)
        return render.api()


#############     API-Funktionen    ################


class ApiDocuments:
    def GET(self):
        """
        API-Methode zur Suche von Dokumenten bzw. zum Abruf eines einzelnen
        Dokuments anhand einer Kennung (reference).
        Ist der URL-Parameter "reference" angegeben, handelt es sich um eine
        Dokumentenabfrage anhand der Kennung(en). Ansonsten ist es eine Suche.
        """
        start = time.time()
        url_params = web.input(reference='', output='', q='*:*', fq='',
                               sort='', start='0', docs='10', date='')
        output = url_params.output.split(',')
        get_attachments = 'attachments' in output
        get_thumbnails = 'thumbnails' in output and get_attachments
        get_consultations = 'consultations' in output
        get_facets = 'facets' in output
        get_relations = 'relations' in output
        request = {}  # Info über die Anfrage
        query = False
        docs = False
        """
        Anhand der übergebenen Parameter wird entschieden, ob eine Solr-Suche
        durchgeführt wird, oder ob die Abfrage direkt anhand von Kennungen
        (references) erfolgen kann.
        """
        references = url_params.reference.replace('-', '/').split(',')
        if len(references) == 1 and references[0] == '':
            # Solr-Suche wird durchgeführt
            q = url_params.q.encode('utf-8')
            query = solr_query(q, fq=url_params.fq, sort=url_params.sort,
                               start=url_params.start, docs=url_params.docs,
                               date=url_params.date,
                               facets=get_facets)
            if query['result']['numhits'] > 0:
                references = query['ids']
            else:
                references = []
            request = query['params']
        else:
            # Direkte Abfrage
            request = {
                'references': references
            }
        request['output'] = output
        # Abrufen der benötigten Dokumente aus der Datenbank
        if len(references) > 0:
            rawdocs = get_documents(references, get_attachments,
                      get_thumbnails, get_consultations, get_relations)
            docs = flatten_doc_dict(rawdocs)

        """
        Im Fall einer Suche beachten wir die richtige Reihenfolge
        und mischen "score" und hightlights mit in die Dokumente.
        Außerdem werden noch ein paar interne Felder entfernt.
        """
        if docs:
            if query:
                sorted_docs = []
                for r in references:
                    if r in docs:
                        if r in query['result']['docs']:
                            if 'score' in query['result']['docs'][r]:
                                docs[r]['score'] = query['result']['docs'][r]['score']
                        if 'highlighting' in query['result'] and r in query['result']['highlighting']:
                            docs[r]['highlighting'] = query['result']['highlighting'][r]
                        sorted_docs.append(docs[r])
                docs = sorted_docs
            else:
                docs = docs.values()
            for doc in docs:
                if 'consultations' in doc and doc['consultations'] is not None:
                    for c in doc['consultations']:
                        if 'submission_id' in c:
                            del c['submission_id']
                        if 'submission_id' in c:
                            del c['request_id']
        ret = {
            'status': 0,
            'duration': int((time.time() - start) * 1000),
            'request': request,
            'response': {}
        }
        if docs:
            ret['response']['documents'] = docs
            ret['response']['numdocs'] = len(docs)
            if query and 'maxscore' in query['result']:
                ret['response']['maxscore'] = query['result']['maxscore']
        if query:
            ret['response']['numhits'] = query['result']['numhits']
            if get_facets and 'facets' in query['result']:
                ret['response']['facets'] = query['result']['facets']
            if 'start' in query['result']:
                ret['response']['start'] = query['result']['start']
        headers(type='application/json', cache_hours=24)
        return json.dumps(ret)


class ApiTerms:
    def GET(self):
        """
        Ausgaben von Stichworten für Autocomplete-Eingabe
        Der Parameter "prefix" dient zum Einschränken der
        Rückgabe auf Begriffe mit einem bestimmten Wortanfang.
        """
        start = time.time()
        url_params = web.input(prefix='')
        prefix = url_params.prefix.strip().encode('utf-8').lower()
        requestdata = {
            'wt': 'json',
            'json.nl': 'arrarr',
            'terms.fl': 'term',
            'terms.prefix': prefix,
            'terms.limit': 10,
            'terms.mincount': 1
        }
        request = urllib2.urlopen(config.SOLR_URL + '/terms',
                                  urllib.urlencode(requestdata))
        response = request.read()
        obj = json.loads(response)
        ret = {
            'duration': int((time.time() - start) * 1000),
            'request': {'prefix': prefix},
            'response': {'terms': obj['terms']['term']}
        }
        headers(type='application/json', cache_hours=24)
        return json.dumps(ret)


class ApiSession:
    def GET(self):
        """
        Setzt Eigenschaften der aktuellen Nutzer-Session
        und gibt Session-Eigenschaften aus.
        Die ausgegebenen Session-Eigenschaften sind:
        location.lat: Position des Nutzer als lat/long Tupel
        location.lon: Position des Nutzer als lat/long Tupel
        location.location_entry: Die Ortsangabe, wie sie der Nutzer zuletzt
            eingegeben hat
        location.resolved: Die Adresse des Nutzers, wie sie interpretiert
            wurde. Dies kann entweder auf Basis der Eingabe oder auf Basis
            von reverse Geocoding passiert sein.
        """
        url_params = web.input(lat=None, lon=None, location_entry=None)
        if url_params.lat is not None and url_params.lon is not None:
            if ('lat' not in session.location or
                'lon' not in session.location or
                url_params.lat != session.location['lat'] or
                url_params.lon != session.location['lon']):
                session.location['lat'] = url_params.lat
                session.location['lon'] = url_params.lon
                reverse_geo = placefinder_reverse_geocode(url_params.lat,
                              url_params.lon)
                if ('ResultSet' in reverse_geo and 'Results'
                    in reverse_geo['ResultSet']
                    and len(reverse_geo['ResultSet']['Results']) > 0):
                    first_result = reverse_geo['ResultSet']['Results'][0]
                    session.location['resolved'] = {
                        'street': first_result['street'],
                        'house': first_result['house'],
                        'postal': first_result['postal']}
        if url_params.location_entry is not None:
            session.location['location_entry'] = url_params.location_entry
        # Liste der auszugebenden Session-Eigenschaften
        ret_keys = ['location']
        session_ret = {}
        for rt in ret_keys:
            if rt in session:
                session_ret[rt] = session[rt]
        headers(type='application/json', cache_hours=0)
        return json.dumps({
            'status': 0,
            'response': {'session': session_ret}
        })


class ApiStreets:
    def GET(self):
        """
        Gibt die Straßen im Umkreis einer Location aus. Der Umkreis
        kann maximal 1000 Meter Radius haben. Es werden maximal
        1000 Straßen ausgegeben, sortiert nach Entfernung zur
        Location.
        """
        start = time.time()
        url_params = web.input(lat='', lon='', radius='500')
        lat = float(url_params.lat.strip())  # geo latitude of search center
        lon = float(url_params.lon.strip())  # geo longitude of search center
        # search radius in meters (max 1000)
        radius = min(1000, int(url_params.radius.strip()))
        earthradius = wgs84_earth_radius(deg2rad(lat))
        (minlat, maxlat, minlon, maxlon) = geo_bounding_box(lat, lon, radius)
        queryvars = dict(lat=lat, lon=lon, minlon=minlon,
                         maxlon=maxlon, minlat=minlat,
                         maxlat=maxlat, radius=radius,
                         earthradius=earthradius)
        results = config.DB.select("""geo_nodes
            LEFT JOIN geo_objects2nodes
                ON geo_objects2nodes.node_id=geo_nodes.id
            LEFT JOIN geo_objects
                ON geo_objects.id=geo_objects2nodes.object_id""",
            queryvars,
            what="""DISTINCT `name`, MIN($earthradius * 2 *
                ASIN(SQRT(POWER(SIN(($lat - ABS(latitude))*pi()/180 / 2), 2)
                + COS($lat * pi()/180) * COS(ABS(latitude) * pi()/180)
                * POWER(SIN(($lon - longitude) *
                pi()/180 / 2), 2) ) )) AS distance""",
            where="""longitude BETWEEN $minlon AND $maxlon AND latitude
                BETWEEN $minlat AND $maxlat""",
            group="geo_objects.name HAVING distance < $radius",
            order="distance ASC",
            limit="1000",
             _test=False)
        rows = []
        for row in results:
            rows.append((row.name, int(row.distance)))
        ret = {
            'duration': int((time.time() - start) * 1000),
            'request': {'lat': lat, 'lon': lon, 'radius': radius},
            'response': {'streets': rows}
        }
        headers(type='application/json', cache_hours=24)
        return json.dumps(ret)


class ApiLocations:
    def GET(self):
        """
        Gibt zu einem Straßennamen wahlweise alle Positionen oder nur den/die
        Mittelpunkt/e aus.
        Mehrere Mittelpunkte kommen vor, wenn eine Straße mehrfach existiert.
        """
        start = time.time()
        url_params = web.input(street='', output='nodes,averages')
        street = url_params.street.strip().encode('utf-8')
        output = url_params.output.strip().split(',')
        status = 0
        if street != '':
            queryvars = dict(name=street)
            results = config.DB.select("""geo_objects
                LEFT JOIN geo_objects2nodes
                    ON geo_objects.id=geo_objects2nodes.object_id
                LEFT JOIN geo_nodes
                    ON geo_objects2nodes.node_id=geo_nodes.id""",
                queryvars,
                what="DISTINCT latitude, longitude",
                where="name=$name AND latitude is not NULL",
                order="longitude, latitude",
                limit="10000",
                 _test=False)
            rows = []
            if len(results) == 0:
                status = 1
                error = 'Nothing found for street'
            else:
                for row in results:
                    rows.append((float(row.latitude), float(row.longitude)))
        else:
            status = 1
            error = 'Missing required parameter: street'
        ret = {
            'request': {},
            'status': status
        }
        if status == 0:
            ret['response'] = {}
            if 'nodes' in output:
                ret['response']['nodes'] = rows
            if 'averages' in output and len(rows) > 0:
                avg_lat = sum([r[0] for r in rows]) / len(rows)
                avg_lon = sum([r[1] for r in rows]) / len(rows)
                ret['response']['averages'] = [(avg_lat, avg_lon)]
        if status == 1:
            ret['error'] = error
        ret['duration'] = int((time.time() - start) * 1000)
        ret['request']['street'] = street
        headers(type='application/json', cache_hours=24)
        return json.dumps(ret)


class ApiGeocode:
    def GET(self):
        """
        Proxy für die Yahoo Placefinder API
        """
        start = time.time()
        url_params = web.input(street='')
        obj = placefinder_geocode(url_params.street)
        obj['duration'] = int((time.time() - start) * 1000)
        headers(type='application/json', cache_hours=24)
        return json.dumps(obj)


############# Datenbank-Abruf, Hilfsfunktionen etc. ###############


def placefinder_geocode(location_string):
    """
    Löst eine Straßen- und optional PLZ-Angabe zu einer Geo-Postion
    auf. Beispiel: "Straßenname (12345)"
    """
    postal = None
    street = location_string.encode('utf-8')
    postalre = re.compile(r'(.+)\s+\(([0-9]{5})\)')
    postal_matching = re.match(postalre, street)
    if postal_matching is not None:
        street = postal_matching.group(1)
        postal = postal_matching.group(2)
    yurl = 'http://where.yahooapis.com/geocode'
    params = {'flags': 'J',  # json
              'appid': config.PLACEFINDER_APP_ID,
              'locale': 'de_DE',
              'street': street,
              'postal': postal,
              'city': config.PLACEFINDER_DEFAULT_CITY,
              'country': config.PLACEFINDER_DEFAULT_COUNTRY}
    try:
        request = urllib2.urlopen(yurl + '?' + urllib.urlencode(params))
        response = request.read()
        try:
            obj = json.loads(response)
            return obj
        except:
            raise web.internalerror()
    except urllib2.HTTPError, e:
        print >> sys.stderr, "FEHLER in placefinder_geocode():", e.code


def placefinder_reverse_geocode(lat, lon):
    yurl = 'http://where.yahooapis.com/geocode'
    params = {
        'flags': 'J',  # json
        'gflags': 'R',
        'appid': config.PLACEFINDER_APP_ID,
        'locale': 'de_DE',
        'location': str(lat) + ' ' + str(lon)}
    try:
        request = urllib2.urlopen(yurl + '?' + urllib.urlencode(params))
        response = request.read()
        try:
            obj = json.loads(response)
            return obj
        except:
            raise web.internalerror()
    except urllib2.HTTPError, e:
        print >> sys.stderr, "FEHLER in placefinder_reverse_geocode():", e.code


def solr_query(q='*:*', sort='', fq='', start=0,
               docs=10, date='', facets=False):
    """
    Führt Suche gegen Solr aus und gibt ein Dict zurück.
    Das Dict hat folgende Einträge:
    ids: Die IDs der Dokumente in der richtigen Sortierung
    result.docs: Die Treffer-Dokumente
    params: Die Qeury-Parameter, die Solr verwendet hat
    result.rows: Anzahl der zurückgegebenen Dokumente
    result.numhits: Anzahl der Treffer, die es zu der Anfrage gibt
    result.start: Index des ersten zurückgegebenen Treffers
    result.maxscore: Höchster score-Wert im gesamten Suchergebnis
    result.highlighting: Felder mit hervorgehobenen Suchbegriffen
    ... (to be continued)
    """
    slr = solr.SolrConnection(config.SOLR_URL)
    sort = sort.strip()
    fq = [fq.strip()]
    start = int(start)
    docs = min(int(docs), 100)
    date_from = None
    date_to = None
    if date.strip() != '':
        (date_from, date_to) = date_range.to_dates(date.strip())
        # Datumsbereich wird als fq Filter hinzugefügt
        fq.append('date:[' + date_from.isoformat() +
                'T00:00:00Z TO ' + date_to.isoformat() + 'T23:59:59Z]')
    if facets == False:
        facets = 'false'
    else:
        facets = 'true'
    if q == '*:*' and sort == '':
        sort = 'date desc'
    else:
        if sort == '':
            sort = 'score desc'
    response = slr.query(q, fields='reference,score',
        score=True, highlight='title', sort=sort,
        rows=docs, fq=fq, start=start, facet=facets)
    # standard return object
    ret = {
        'status': response.header['status'],
        'querytime': response.header['QTime']
    }
    params_to_return = ['q', 'fq', 'sort', 'rows', 'start']
    if 'params' in response.header:
        ret['params'] = {}
        for param in params_to_return:
            if param in response.header['params']:
                ret['params'][param] = response.header['params'][param]
    if int(response.header['status']) == 0:
        ret['result'] = {}
        ret['result']['rows'] = len(response)
        ret['result']['numhits'] = int(response.results.numFound)
        if int(response.results.numFound) > 0:
            if len(response) > 0:
                # IDs sammeln
                ret['ids'] = [doc['reference'] for doc in response.results]
                ret['result']['sort'] = sort
                ret['result']['start'] = int(response.results.start)
                ret['result']['docs'] = parse_result_docs(response.results)
                ret['result']['maxscore'] = float(response.results.maxScore)
            if len(response) > 0 and hasattr(response, 'highlighting'):
                ret['result']['highlighting'] = response.highlighting
            if hasattr(response, 'facet_counts'):
                facet_fields = response.facet_counts['facet_fields']
                ret['result']['facets'] = {
                    'committee': facet_fields['committee'],
                    'person': facet_fields['person'],
                    'type': facet_fields['type'],
                    'street': facet_fields['street'],
                    'term': facet_fields['term'],
                    'date': parse_result_daterange_monthly(
                        response.facet_counts['facet_ranges']['date'])
                }
    return ret


def get_documents(references, get_attachments=False, get_thumbnails=False,
    get_consultations=False, get_relations=False):
    """
    Liest Dokumente mit den gegebenen IDs aus der Datenbank. Wenn entsprechend
    angegeben, werden auch Anlagen, Thumbnails und die Beratungsfolge mit
    zurück gegeben.
    """
    if len(references) == 1 and references[0] == '':
        return None
    requests = config.DB.select('requests',
                    dict(references=references),
                    where='request_identifier IN $references',
                    what='''request_id, committee_id, request_date,
                        request_identifier, request_subject''')
    submissions = config.DB.select('submissions',
                    dict(references=references),
                    where='submission_identifier IN $references',
                    what='''submission_id, submission_date,
                        submission_identifier, submission_subject,
                        submission_type''')
    docs = {}
    request_ids = []
    submission_ids = []
    if len(requests) > 0:
        for e in requests:
            if e['request_identifier'] not in docs:
                docs[e['request_identifier']] = []
            docs[e['request_identifier']].append({
                'type': 'request',
                'id': e['request_id'],
                'date': e['request_date'],
                'reference': e['request_identifier'],
                'title': e['request_subject'],
                'url': config.BASE_URL + 'dokumente/' +
                    e['request_identifier'].replace('/', '-') + '/',
                'original_url': config.RIS_AG_URLPATTERN % e['request_id']
            })
            request_ids.append(e['request_id'])
    if len(submissions) > 0:
        for e in submissions:
            if e['submission_identifier'] not in docs:
                docs[e['submission_identifier']] = []
            docs[e['submission_identifier']].append({
                'type': 'submission',
                'submission_type': e['submission_type'],
                'id': e['submission_id'],
                'date': e['submission_date'],
                'reference': e['submission_identifier'],
                'title': e['submission_subject'],
                'url': config.BASE_URL + 'dokumente/' +
                    e['submission_identifier'].replace('/', '-') + '/',
                'original_url': config.RIS_VO_URLPATTERN % e['submission_id']
            })
            submission_ids.append(e['submission_id'])
    if len(docs) == 0:
        return None
    else:
        # Gemeinsame Nachbearbeitung
        for key in docs.keys():
            for n in range(0, len(docs[key])):
                if docs[key][n]['date'] is not None:
                    docs[key][n]['date'] = (
                        docs[key][n]['date'].strftime('%Y-%m-%d'))

    """
    Sammle Attachments für alle Requests und Submissions
    Das sind einige verschachtelte Iterationen - da gibt
    es Optimierungspotential. Allerdings würde das die
    SQL-Abfrage in get_attachments_for_documents() verkom-
    plizieren.
    """
    if get_attachments:
        request_attachments = None
        submission_attachments = None
        if len(request_ids) > 0:
            request_attachments = get_attachments_for_documents(request_ids,
                'request', get_thumbnails)
        if len(submission_ids) > 0:
            submission_attachments = get_attachments_for_documents(
                submission_ids, 'submission', get_thumbnails)
        if request_attachments is not None:
            for attachment in request_attachments:
                for key in docs.keys():
                    for n in range(0, len(docs[key])):
                        if (docs[key][n]['type'] == 'request' and
                                docs[key][n]['id'] ==
                                attachment['request_id']):
                            if 'attachments' not in docs[key][n]:
                                docs[key][n]['attachments'] = []
                            docs[key][n]['attachments'].append(attachment)
        if submission_attachments is not None:
            for attachment in submission_attachments:
                for key in docs.keys():
                    for n in range(0, len(docs[key])):
                        if (docs[key][n]['type'] == 'submission' and
                                docs[key][n]['id'] ==
                                attachment['submission_id']):
                            if 'attachments' not in docs[key][n]:
                                docs[key][n]['attachments'] = []
                            docs[key][n]['attachments'].append(attachment)
    # Beratungsfolge abholen
    if get_consultations:
        request_consultations = None
        submission_consultations = None
        if len(request_ids) > 0:
            #print "request_ids", request_ids
            request_consultations = get_consultations_for_document(
                request_ids, 'request')
        if len(submission_ids) > 0:
            submission_consultations = get_consultations_for_document(
                    submission_ids, 'submission')
        if request_consultations is not None:
            for con in request_consultations:
                for key in docs.keys():
                    for n in range(0, len(docs[key])):
                        if (docs[key][n]['type'] == 'request'
                            and docs[key][n]['id'] ==
                            con['request_id']):
                            if 'consultations' not in docs[key][n]:
                                docs[key][n]['consultations'] = []
                            docs[key][n]['consultations'].append(con)
        if submission_consultations is not None:
            for consultation in submission_consultations:
                for key in docs.keys():
                    for n in range(0, len(docs[key])):
                        if (docs[key][n]['type'] == 'submission'
                                and docs[key][n]['id'] ==
                                consultation['submission_id']):
                            if 'consultations' not in docs[key][n]:
                                docs[key][n]['consultations'] = []
                            docs[key][n]['consultations'].append(consultation)
    # Dokumenten-Beziehungen
    #if get_relations:
    #    for key in docs.keys():
    #        docs[key]['relationships'] = get_relationships_for_document(key)
    # Nachbearbeitung der Daten für die Ausgabe
    for key in docs.keys():
        for doc in docs[key]:
            # Leere Eintraege entfernen
            if 'attachments' in doc:
                if 'request_id' in doc['attachments']:
                    del doc['attachments']['request_id']
                if 'submission_id' in doc['attachments']:
                    del doc['attachments']['submission_id']
            if 'consultations' in doc:
                if 'request_id' in doc['consultations']:
                    del doc['consultations']['request_id']
                if 'submission_id' in doc['consultations']:
                    del doc['consultations']['submission_id']
            if 'id' in doc:
                del doc['id']
            # Typ umschreiben
            if doc['type'] == 'request':
                doc['type'] = 'Antrag'
            if 'submission_type' in doc:
                doc['type'] = doc['submission_type']
                del doc['submission_type']
    return docs


def flatten_doc_dict(docs):
    """
    Formt das Dokumenten-Dict um. Dabei werden Duplikate, also
    mehrere Dokumente mit der selben Kennung (reference) je einem
    Eintrag zusammen gefasst. Damit wird die Kölner Eigenart, dass
    in Einzelfällen mehrere (meist identische) Dokumente die selbe
    Kennung haben, ausgebügelt.
    """
    if docs is None:
        return None
    references = docs.keys()
    out = {}
    for r in references:
        doc = {}
        for n in range(0, len(docs[r])):
            for key in docs[r][n].keys():
                if key not in doc:
                    doc[key] = []
                for element in tolist(docs[r][n][key]):
                    doc[key].append(element)
        # Identische Elemente in Listen entfernen
        for key in doc.keys():
            if type(doc[key][0]).__name__ in ['str', 'unicode']:
                doc[key] = unique(doc[key])
            # bestimmte Attribute sollen keine Listen sein
            if key in ['reference', 'url']:
                doc[key] = unlist(doc[key])
        out[r] = doc
    return out


def tolist(s):
    """
    Falls das Objekt keine Liste ist, gibt die Funktion eine Liste
    zurück, indem das Objekt das einzige Element ist.
    """
    if type(s).__name__ == 'list':
        return s
    return [s]


def unlist(l):
    """
    Macht aus einer Liste mit nur einem Element einen Skalar.
    """
    if len(l) == 1:
        return l[0]
    return l


def unique(l):
    """
    Entfernt doppelt vorkommende Werte aus einer Liste. Die Reihenfolge
    der Elemente wird dabei nicht berücksichtigt.
    """
    keys = {}
    for e in l:
        keys[e] = True
    return keys.keys()


def byte_to_mb(byte):
    """convert bytes to megabytes"""
    return byte / 1024.0 / 1024.0


def parse_result_docs(docs):
    """
    Parst Solr-Dokumentendaten, so dass sie JSON-tauglich sind
    """
    ret = {}
    for doc in docs:
        newdoc = {}
        for key in doc.keys():
            thetype = type(doc[key]).__name__
            if thetype == 'datetime.datetime':
                newdoc[key] = doc[key].strftime('%Y-%m-%d')
            elif thetype == 'unicode':
                newdoc[key] = doc[key].strip()
            else:
                newdoc[key] = doc[key]
        ret[newdoc['reference']] = newdoc
    return ret


def parse_result_daterange_monthly(doc):
    """
    Parses date range facets so that the dicts are
    formatted ideally for the +1MONTH gap
    """
    ret = {}
    for key in doc.keys():
        if key in ['start', 'end']:
            ret[key] = doc[key].strftime('%Y-%m-%d')[0:7]
        elif key == 'counts':
            ret[key] = {}
            for datekey in doc[key].keys():
                ret[key][datekey[0:7]] = doc[key][datekey]
    return ret


def rfc1123date(value):
    """
    Gibt ein Datum (datetime) im HTTP Head-tauglichen Format (RFC 1123) zurück
    """
    stamp = time.mktime(value.timetuple())
    return formatdate(timeval=stamp, localtime=False, usegmt=True)


def get_attachments_for_documents(dids, dtype, get_thumbnails=False):
    """
    Liest die Anhänge (attachments) zu den Dokumenten mit den übergebenen
    IDs aus der Datenbank und gibt sie zurück. Wenn Anhänge vorhanden waren
    aber gelöscht wurden, wird dies ebenfalls ausgegeben.
    """
    queryvars = dict(did=dids)
    thetable = None
    thewhere = ''
    thewhat = '''attachments.attachment_id AS id, attachment_role AS role,
        attachment_mimetype AS type, attachment_filename AS filename,
        attachment_size AS size, attachment_content AS content,
        attachment_lastmod AS last_modified, sha1_checksum,
        (MAX(page)+1) AS numpages,
        excluded_since, reason_code, reason_text'''
    group = ''
    if dtype == 'request':
        thewhat += ', request_id'
        thetable = '''requests2attachments LEFT JOIN attachments
            ON requests2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN attachment_exclusions
            ON attachment_exclusions.attachment_id=attachments.attachment_id
            LEFT JOIN attachment_thumbnails
            ON attachments.attachment_id=attachment_thumbnails.attachment_id'''
        thewhere = 'request_id IN $did AND attachment_filename IS NOT NULL'
        group = 'attachments.attachment_id'
    elif dtype == 'submission':
        thewhat += ', submission_id'
        thetable = '''submissions2attachments LEFT JOIN attachments
            ON submissions2attachments.attachment_id=attachments.attachment_id
            LEFT JOIN attachment_exclusions
            ON attachment_exclusions.attachment_id=attachments.attachment_id
            LEFT JOIN attachment_thumbnails
            ON attachments.attachment_id=attachment_thumbnails.attachment_id'''
        thewhere = 'submission_id IN $did AND attachment_filename IS NOT NULL'
        group = 'attachments.attachment_id'
    result = config.DB.select(thetable, queryvars,
            what=thewhat, where=thewhere, group=group)
    if len(result) > 0:
        rows = []
        attachment_ids = []
        # Strukturierung des Ergebnisses
        for row in result:
            attachment_ids.append(row['id'])
            row['url'] = attachment_url(row['id'], row['filename'])
            if 'last_modified' in row and row['last_modified'] is not None:
                row['last_modified'] = row['last_modified'].strftime('%Y-%m-%dT%H:%M:%SZ')
            if row['content'] == '':
                row['content'] = None
            if get_thumbnails:
                row['thumbnails'] = get_attachment_thumbnails([row['id']])
            row['exclusion'] = None
            if row['excluded_since'] is not None:
                row['exclusion'] = {
                    'reason_code': row['reason_code'],
                    'reason_text': row['reason_text'],
                    'date': row['excluded_since'].strftime('%Y-%m-%dT%H:%M:%SZ')}
                row['url'] = None
            del row['reason_code']
            del row['reason_text']
            del row['excluded_since']
            rows.append(row)
        return rows


def get_relationships_for_document(reference, attachment_ids=None):
    """
    Gibt die Beziehungen, die von einem Dokument ausgehen, zurück.
    Parameter:
    * reference: Dokumenten-ID
    * attachment_ids: Liste der Attachment-IDs des Dokuments
    """
    # TODO: entsprechende Eintraege auslesen
    pass


def attachment_url(id, filename):
    """
    Erstellt aus der Attachment-ID und dem ursprünglichen Dateinamen
    die richtige URL
    """
    extension = filename.split('.')[-1]
    url = (config.BASE_URL + 'attachments/' + str(id)[-1] + '/'
        + str(id)[-2] + '/' + extension + str(id) + '.' + extension)
    return url


def attachment_thumbnail_url(id, filename):
    """
    Erstellt aus der Attachment-ID und dem Thumbnail-Dateinamen
    die komplette URL
    """
    url = (config.BASE_URL + 'static/thumbs/' + str(id)[-1] + '/' +
        str(id)[-2] + '/' + filename)
    return url


def get_attachment_thumbnails(attachment_ids):
    """
    Liefert die Thumbnails für die Dateianhänge mit den übergebenen
    attachment_ids zurück
    """
    result = config.DB.select('attachment_thumbnails',
        dict(attachment_id=attachment_ids),
        where='attachment_id IN $attachment_id',
        what='attachment_id, filename, width, height, page',
        order='filename')
    if len(result) > 0:
        rows = []
        for row in result:
            row['url'] = attachment_thumbnail_url(row['attachment_id'],
                row['filename'])
            del row['filename']
            del row['attachment_id']
            rows.append(row)
        return rows


def get_consultations_for_document(dids, dtype):
    """
    Liest die Tagesordnungspunkte (agendaitems) zu den Dokumenten
    mit den übergebenen IDs aus der Datenbank und gibt sie zurück
    """
    if dids is None or len(dids) == 0:
        return None
    queryvars = dict(did=dids)
    thetable = None
    thewhere = ''
    thewhat = '''agendaitem_identifier AS agendaitem_number,
        agendaitem_subject AS agendaitem_title, agendaitem_result,
        session_identifier AS session_reference, session_date AS date,
        session_description, sessions.committee_id,
        committee_title AS committee_name'''
    if dtype == 'request':
        thewhat += ', request_id'
        thetable = '''agendaitems2requests LEFT JOIN agendaitems
            ON agendaitems2requests.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions
                ON sessions.session_id=agendaitems.session_id
            LEFT JOIN committees
                ON sessions.committee_id=committees.committee_id'''
        thewhere = 'request_id IN $did'
    elif dtype == 'submission':
        thewhat += ', submission_id'
        thetable = '''agendaitems2submissions
            LEFT JOIN agendaitems
            ON agendaitems2submissions.agendaitem_id=agendaitems.agendaitem_id
            LEFT JOIN sessions
            ON sessions.session_id=agendaitems.session_id
            LEFT JOIN committees
            ON sessions.committee_id=committees.committee_id'''
        thewhere = 'submission_id IN $did'
    result = config.DB.select(thetable, queryvars, what=thewhat,
        where=thewhere, order='session_date ASC')
    if len(result) > 0:
        rows = []
        for row in result:
            if 'date' in row and row['date'] is not None:
                row['date'] = row['date'].strftime('%Y-%m-%d')
            rows.append(row)
        return rows


def valid_document_reference(string):
    # e.g. "AN/0123/4567"
    match1 = re.match(r'[A-Z]{2}\/[0-9]{4,5}\/[0-9]{4}', string)
    # e.g. "1234/5678"
    match2 = re.match(r'[0-9]{4}\/[0-9]{4}', string)
    # e.g. "1234/5678/1"
    match3 = re.match(r'[0-9]{4}\/[0-9]{4}\/[0-9]{1,2}', string)
    if match1 is not None or match2 is not None or match3 is not None:
        return True
    return False


def deg2rad(deg):
    """Grad in Radians konvertieren"""
    return math.pi * deg / 180.0


def rad2deg(rad):
    """Radians in Grad konvertieren"""
    return 180.0 * rad / math.pi


def wgs84_earth_radius(lat):
    """
    Erdradius in Abhängigkeit von der Breite
    entsprechend WGS-84 Ellipsoid"""
    # Semi-axes of WGS-84 geoidal reference
    WGS84_a = 6378137.0  # Major semiaxis [m]
    WGS84_b = 6356752.3  # Minor semiaxis [m]
    An = WGS84_a * WGS84_a * math.cos(lat)
    Bn = WGS84_b * WGS84_b * math.sin(lat)
    Ad = WGS84_a * math.cos(lat)
    Bd = WGS84_b * math.sin(lat)
    return math.sqrt((An * An + Bn * Bn) / (Ad * Ad + Bd * Bd))


def geo_bounding_box(lat, lon, half_side):
    """
    Berechnet die Bounding Box um einen Mittelpunkt und gibt
    sie als Vierer-Tupel zurück (minlat, maxlat, minlon, maxlong).
    Die Bounding Box ist ein Rechteck (Quadrat), dass einen gedachten
    Kreis mit dem gegebenen Radius um einen Punkt auf der Erdoberfläche
    umschließt.
    Parameter:
    lat: Breite in Dezimalgrad (float)
    lon: Länge in Dezimalgrad (float)
    half_side: radius des inneren Kreises bzw. halbe Seitenlänge in
                   Metern (int)
    """
    lat = deg2rad(lat)
    lon = deg2rad(lon)
    # Hartkodierte Korrektur. Nicht ganz zu erklären, warum das nötig ist.
    # Mit Faktor 1 wird der angegebene Radius - zumindest nach der Distanz-
    # Funktion in api_streets nicht voll ausgefülllt.
    half_side = half_side * 1.0
    # Erdradius bei gegebener Breite
    radius = wgs84_earth_radius(lat)
    pradius = radius * math.cos(lat)
    lat_min = lat - half_side / radius
    lat_max = lat + half_side / radius
    lon_min = lon - half_side / pradius
    lon_max = lon + half_side / pradius
    return (rad2deg(lat_min), rad2deg(lat_max),
        rad2deg(lon_min), rad2deg(lon_max))


def headers(type=None, cache_hours=None):
    """
    Sendet typische HTTP-Header wie content-type, expires und Cache-control
    """
    if type is not None:
        web.header('Content-Type', type)
    if cache_hours is not None:
        if cache_hours == 0:
            web.header('Cache-Control', 'no-cache')
            web.header('Pragma', 'no-cache')
        else:
            web.header('Expires', rfc1123date(datetime.datetime.now() +
                   datetime.timedelta(hours=cache_hours)))
            seconds = cache_hours * 60 * 60
            web.header('Cache-Control', 'max-age=' + str(seconds))


app = web.application(urls, globals())
store = web.session.DBStore(config.DB, config.HTTP_SESSION_TABLE_NAME)
session = web.session.Session(app, store, initializer={'location': {}})
render = web.template.render(config.BASE_PATH + os.sep + 'templates/', base="layout",
    globals={'context': session})

if __name__ == "__main__":
    try:
        # benoetigt für FastCGI
        import flup.server.fcgi as flups
        web.wsgi.runwsgi = lambda func, addr=None: web.wsgi.runfcgi(func, addr)
    except:
        print """Info: Not running in FastCGI/WSGI environment.
            Module flup.server.fcgi not available."""
    app.run()
