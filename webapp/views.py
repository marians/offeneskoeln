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

# Don't know about these yet
#from __future__ import absolute_import
#from __future__ import division
#from __future__ import print_function

import pprint
import os
import json
import util
import db
import datetime
import time
import urllib

from flask import abort
from flask import render_template
from flask import make_response
from flask import request
from flask import redirect
from flask import Response
from flask import Markup

from webapp import app

#import webapp.date_range
#import config


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/api/")
def api_home():
    return render_template('api.html')


@app.route("/ueber/")
def ueber():
    return render_template('ueber.html')


@app.route("/daten/")
def daten():
    """
    Anzeige der /daten Seite mit Auflistung der
    Download-Dateien
    """
    filelist = []
    path = app.config['BASE_PATH'] + os.sep + 'daten'
    for filename in os.listdir(path):
        filepath = path + os.sep + filename
        stat = os.lstat(filepath)
        if os.path.isfile(filepath) or os.path.islink(filepath):
            filelist.append({
                'name': filename,
                'size': "%d" % (stat.st_size / 1024.0 / 1024.0),
            })
    return render_template('daten.html', filelist=filelist)


@app.route("/disclaimer/")
def disclaimer():
    return render_template('disclaimer.html')


@app.route("/favicon.ico")
def favicon():
    return ""


@app.route("/attachments/<path:download_path>")
def legacy_attachment(download_path):
    """
    Download-Redirect für veraltete URLs auf offeneskoeln.de.
    Siehe https://github.com/marians/offeneskoeln/wiki/Neue-Attachment-URLs-und-Redirects
    """
    new_url = db.map_download_url(download_path)
    if new_url is None:
        abort(404)
        # TODO: Rendere informativere 404 Seite
    else:
        return redirect(new_url, 301)


@app.route("/anhang/download/<string:attachment_id>.<string:extension>")
def attachment_download(attachment_id, extension):
    return attachment_view(attachment_id=attachment_id,
        extension=extension,
        savefile=True)


@app.route("/anhang/<string:attachment_id>.<string:extension>")
def attachment_view(attachment_id, extension, savefile=False):
    """
    Abruf/Download eines Attachments
    """
    attachment_info = db.get_attachment(attachment_id)
    #pprint.pprint(attachment_info)
    if attachment_info is None:
        # TODO: Rendere informativere 404 Seite
        abort(404)
    # extension doesn't match file extension (avoiding arbitrary URLs)
    proper_extension = attachment_info['filename'].split('.')[-1]
    if proper_extension != extension:
        abort(404)

    # 'file' property is not set (e.g. due to depublication)
    if 'file' not in attachment_info:
        if 'depublication' in attachment_info:
            abort(410)  # Gone
        else:
            # TODO: log this as unexplicable...
            abort(500)

    # handle conditional GET
    if 'If-Modified-Since' in request.headers:
        file_date = attachment_info['file']['uploadDate'].replace(tzinfo=None)
        request_date = util.parse_rfc1123date(request.headers['If-Modified-Since'])
        difference = file_date - request_date
        if difference < datetime.timedelta(0, 1):  # 1 second
            return Response(status=304)

    #if 'if-none-match' in request.headers:
    #    print "Conditional GET: If-None-Match"
    # TODO: handle ETag in request

    handler = db.get_file(attachment_info['file']['_id'])
    response = make_response(handler.read(), 200)
    response.mimetype = attachment_info['mimetype']
    response.headers['X-Robots-Tag'] = 'noarchive'
    response.headers['ETag'] = attachment_info['sha1']
    response.headers['Last-modified'] = util.rfc1123date(
                    attachment_info['file']['uploadDate'])
    response.headers['Expires'] = util.expires_date(
                                        hours=(24 * 30))
    response.headers['Cache-Control'] = util.cache_max_age(
                                            hours=(24 * 30))
    # Save to file option
    if savefile == True:
        response.headers['Content-Disposition'] = 'attachment; filename=%s' % attachment_info['filename']
        response.headers['X-Robots-Tag'] = 'noindex'
        # See https://support.google.com/webmasters/answer/139394
        response.headers['Link'] = '<%sanhang/%s.%s>; rel="canonical"' % (
            app.config['BASE_URL'], attachment_id, extension)
    return response


@app.route("/suche/")
def suche():
    """
    URL-Parameter:
    q: Suchanfrage, nutzer-formuliert
    fq: Filter query (Lucene Syntax)
    sort: Sortierung, z.B. "id asc"
    start: Offset im Suchergebnis
    num: Anzahl der Treffer pro Seite
    date: Datumsbereich als String
    """
    search_settings = {}
    search_settings['q'] = request.args.get('q', '')
    search_settings['fq'] = request.args.get('fq', '')
    search_settings['sort'] = request.args.get('sort', '')
    search_settings['start'] = int(request.args.get('start', '0'))
    search_settings['num'] = int(request.args.get('num', '10'))
    search_settings['num'] = min(search_settings['num'], 100)  # max 100 items
    search_settings['date'] = request.args.get('date', '')
    html = render_template('suche.html', search_settings=search_settings)
    response = make_response(html, 200)
    response.headers['Expires'] = util.expires_date(hours=24)
    response.headers['Cache-Control'] = util.cache_max_age(hours=24)
    return response


@app.route("/dokumente/")
def dokumente_liste():
    """
    Gibt eine sehr simple Liste aller Dokumente mit Links zur
    Detailseite aus.
    """
    documents = db.get_all_submission_identifiers()
    #pprint.pprint(documents)
    return render_template('dokument_liste.html', documents=documents)


@app.route("/dokumente/<path:identifier>/")
def dokument(identifier):
    """
    Gibt Dokumenten-Detailseite aus
    """
    result = db.get_submissions(references=[identifier],
                        get_attachments=True,
                        get_consultations=True,
                        get_thumbnails=True)
    if len(result) == 0:
        abort(404)
    return render_template('dokument_detailseite.html', submission=result[0])


@app.template_filter('urlencode')
def urlencode_filter(s):
    if type(s) == Markup:
        s = s.unescape()
    s = s.encode('utf8')
    s = urllib.quote_plus(s)
    return Markup(s)


@app.template_filter('debug')
def debug_filter(s):
    pprint.pprint(s)
    return s
