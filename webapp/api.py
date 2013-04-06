# encoding: utf-8

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

import pprint
import os
import json
import util
import db
import datetime
import time

from flask import Flask
from flask import abort
from flask import render_template
from flask import make_response
from flask import request
from flask import redirect
from flask import Response

import werkzeug

from webapp import app


@app.route("/api/documents")
def api_documents():
    """
    API-Methode zur Suche von Dokumenten bzw. zum Abruf eines einzelnen
    Dokuments anhand einer Kennung (reference).
    Ist der URL-Parameter "reference" angegeben, handelt es sich um eine
    Dokumentenabfrage anhand der Kennung(en). Ansonsten ist es eine Suche.
    """
    start_time = time.time()
    ref = request.args.get('reference', '')
    references = ref.split(',')
    output = request.args.get('output', '').split(',')
    q = request.args.get('q', '*:*')
    fq = request.args.get('fq', '')
    sort = request.args.get('sort', '')
    start = request.args.get('start', '0')
    docs = request.args.get('docs', '10')
    date_param = request.args.get('date', '')
    get_attachments = 'attachments' in output
    get_thumbnails = 'thumbnails' in output and get_attachments
    get_consultations = 'consultations' in output
    get_facets = 'facets' in output
    get_relations = 'relations' in output
    request_info = {}  # Info über die Anfrage
    query = False
    docs = False
    # TODO: entscheiden, was mit get_relations passiert
    """
    Anhand der übergebenen Parameter wird entschieden, ob eine Solr-Suche
    durchgeführt wird, oder ob die Abfrage direkt anhand von Kennungen
    (references) erfolgen kann.
    """
    if len(references) == 1 and references[0] == '':
        # Suche wird durchgeführt
        # (References-Liste via Suchmaschine füllen)
        abort(500)
        # TODO
        query = db.query_submissions(q, fq=fq, sort=sort, start=start,
                           docs=docs, date=date_param, facets=get_facets)
        if query['result']['numhits'] > 0:
            references = query['ids']
        else:
            references = []
        request_info = query['params']
    else:
        # Direkte Abfrage
        request_info = {
            'references': references
        }
    request_info['output'] = output

    # Abrufen der benötigten Dokumente aus der Datenbank
    if len(references) > 0:
        docs = db.get_submissions(references=references,
                        get_attachments=get_attachments,
                        get_consultations=get_consultations,
                        get_thumbnails=get_thumbnails)
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

        for doc in docs:
            if 'consultations' in doc and doc['consultations'] is not None:
                for c in doc['consultations']:
                    if 'submission_id' in c:
                        del c['submission_id']
                    if 'submission_id' in c:
                        del c['request_id']
    ret = {
        'status': 0,
        'duration': int((time.time() - start_time) * 1000),
        'request': request_info,
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

    json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
    response = make_response(json_output, 200)
    response.mimetype = 'application/json'
    response.headers['Expires'] = util.expires_date(hours=24)
    response.headers['Cache-Control'] = util.cache_max_age(hours=24)
    return response
