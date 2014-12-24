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

import os
import json
import util
import db
import datetime
import time
import urllib
import sys
import re

from flask import abort
from flask import render_template
from flask import make_response
from flask import request
from flask import redirect
from flask import Response
from flask import Markup
from flask import session
from flask.ext.basicauth import BasicAuth
from bson import ObjectId, DBRef

from webapp import app, mongo, basic_auth
from forms import *


@app.route("/")
def index():
  return render_template('index.html', session=session)


@app.route("/api/")
def api_home():
  return render_template('api.html')


@app.route("/hilfe/")
def hilfe():
  return render_template('hilfe.html')

@app.route("/ueber/")
def ueber():
  return render_template('ueber.html')

@app.route("/impressum/")
def impressum():
  return render_template('impressum.html')

@app.route("/daten/")
def daten():
  """
  Anzeige der /daten Seite mit Auflistung der
  Download-Dateien
  """
  path = app.config['DB_DUMP_FOLDER'] + os.sep + app.config['RS'] + '.tar.bz2'
  if os.path.isfile(path):
    stat = os.lstat(path)
    databasefilesize = "%d" % (stat.st_size / 1024.0 / 1024.0)
  else:
    databasefilesize = 0
  path = app.config['ATTACHMENT_FOLDER'] + os.sep + app.config['RS'] + '.tar.bz2'
  if os.path.isfile(path):
    stat = os.lstat(path)
    attachmentsfilesize = "%d" % (stat.st_size / 1024.0 / 1024.0 / 1024.0)
  else:
    attachmentsfilesize = 0
  return render_template('daten.html', databasefilesize=databasefilesize, attachmentsfilesize=attachmentsfilesize)


@app.route("/disclaimer/")
def disclaimer():
  return render_template('disclaimer.html')


@app.route("/favicon.ico")
def favicon():
  return ""

@app.route("/data/<filename>")
def data_download(filename):
  return ""


@app.route("/robots.txt")
def robots_txt():
  return render_template('robots.txt')


@app.route("/anhang/<string:attachment_id>.<string:extension>")
def attachment_download(attachment_id, extension):
  """
  Download eines Attachments
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
  #  print "Conditional GET: If-None-Match"
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
  search_settings['r'] = request.form.get('r')
  if not search_settings['r']:
    search_settings['r'] = request.args.get('r', app.config['region_default'])
  search_settings['q'] = request.args.get('q', '')
  search_settings['fq'] = request.args.get('fq', '')
  search_settings['sort'] = request.args.get('sort', '')
  search_settings['start'] = int(request.args.get('start', '0'))
  search_settings['ppp'] = int(request.args.get('ppp', '10'))
  search_settings['ppp'] = min(search_settings['ppp'], 100)  # max 100 items
  search_settings['date'] = request.args.get('date', '')
  html = render_template('suche.html', search_settings=search_settings)
  response = make_response(html, 200)
  response.headers['Expires'] = util.expires_date(hours=24)
  response.headers['Cache-Control'] = util.cache_max_age(hours=24)
  return response

@app.route("/paper/<path:id>/")
def view_paper(id):
  """
  Gibt Dokumenten-Detailseite aus
  """
  result = db.get_paper(search_params = {'_id': ObjectId(id)},
                        deref = {'values': ['body', 'mainFile', 'auxiliaryFile', 'subordinatedPaper', 'superordinatedPaper']})
  if len(result) == 0:
    abort(404)
  result = result[0]
  result['numberOfFiles'] = 0
  if 'mainFile' in result:
    result['numberOfFiles'] += 1
  if 'auxiliaryFile' in result:
    result['numberOfFiles'] += len(result['auxiliaryFile'])
  result['consultation'] = db.get_consultation(search_params = {'paper': DBRef('paper', ObjectId(id))})
  for consultation_id in range(len(result['consultation'])):
    #print result['consultation'][consultation_id]
    agendaItem_result = db.get_agendaItem(search_params = {'consultation': DBRef('consultation', result['consultation'][consultation_id]['_id'])})
    if len(agendaItem_result):
      result['consultation'][consultation_id]['agendaItem'] = agendaItem_result[0]
      meeting_result = db.get_meeting(search_params = {'agendaItem': DBRef('agendaItem', result['consultation'][consultation_id]['agendaItem']['_id'])})
      if len(meeting_result):
        result['consultation'][consultation_id]['agendaItem']['meeting'] = meeting_result[0]
  """references=[identifier],
    get_attachments=True,
    get_consultations=True,
    get_thumbnails=True)"""
  return render_template('paper_details.html', paper=result)

#@app.route("/admin")
#@app.route("/admin/<string:funct>")
#@basic_auth.required
#def admin(funct):
#  if funct == 'responses':
#    responses=db.get_responses()
#    for response in responses:
#      response['response_type'] = app.config['RESPONSE_IDS'][response['response_type']]
#    return render_template('admin_response.html', responses=responses)
#  return render_template('admin.html')

@app.route('/admin/config', methods=['GET', 'POST'])
@basic_auth.required
def admin_config():
  if request.method == 'POST':
    config_form = ConfigForm(request.form)
    config_form.config.data = json.dumps(json.loads(config_form.config.data), cls=util.MyEncoder, sort_keys=True, indent=2, ensure_ascii=False)
  else:
    config = []
    for value in mongo.db.config.find():
      if '_id' in value:
        del value['_id']
      config.append(value)
    if len(config) == 1:
      config = config[0]
    else:
      config = {}
    config = json.dumps(config, cls=util.MyEncoder, sort_keys=True, indent=2, ensure_ascii=False)
    config_form = ConfigForm(config=config)
  if request.method == 'POST' and config_form.validate():
    config = json.loads(config_form.config.data)
    mongo.db.config.remove({})
    mongo.db.config.insert(config)
  return render_template('admin_config.html', config_form=config_form)

@app.route('/admin/regions', methods=['GET', 'POST'])
@basic_auth.required
def admin_regions():
  return render_template('admin_regions.html', regions=mongo.db.region.find())

@app.route('/admin/region/new', methods=['GET', 'POST'])
@basic_auth.required
def admin_region_new():
  if request.method == 'POST':
    region_form = RegionForm(request.form)
  else:
    region_form = RegionForm()
  if request.method == 'POST' and region_form.validate():
    new_region_bodies = region_form.bodies.data.replace("\r", "").split("\n")
    new_region_keywords = region_form.keywords.data.replace("\r", "").split("\n")
    save_region_bodies = []
    for current_body in new_region_bodies:
      save_region_bodies.append(DBRef('body', current_body))
    mongo.db.region.insert({'name': region_form.name.data,
                            'type': region_form.type.data,
                            'lat': region_form.lat.data,
                            'lon': region_form.lon.data,
                            'zoom': region_form.zoom.data,
                            'body': save_region_bodies,
                            'keyword': new_region_keywords})
    return redirect('/admin/regions')
  return render_template('admin_region_new.html', region_form=region_form)

@app.route('/admin/region/edit', methods=['GET', 'POST'])
@basic_auth.required
def admin_region_edit():
  if request.method == 'POST':
    region_form = RegionForm(request.form)
  else:
    config = []
    for value in mongo.db.region.find({'_id': ObjectId(request.args.get('id'))}):
      config.append(value)
    if len(config) == 1:
      bodies = []
      for body in config[0]['body']:
        bodies.append(str(body.id))
      region_form = RegionForm(name = config[0]['name'],
                               type = int(config[0]['type']) if 'type' in config[0] else 0,
                               lat = config[0]['lat'] if 'lat' in config[0] else 0.0,
                               lon = config[0]['lon'] if 'lon' in config[0] else 0.0,
                               zoom = config[0]['zoom'] if 'zoom' in config[0] else 0.0,
                               bodies = "\n".join(bodies),
                               keywords = "\n".join(config[0]['keyword']) if 'keyword' in config[0] else '')
    else:
      abort(500)
  if request.method == 'POST' and region_form.validate():
    region_bodies = region_form.bodies.data.replace("\r", "").split("\n")
    save_region_keywords = region_form.keywords.data.replace("\r", "").split("\n")
    save_region_bodies = []
    for current_body in region_bodies:
      save_region_bodies.append(DBRef('body', re.sub('\s+', '', current_body)))
    mongo.db.region.update({'_id': ObjectId(request.args.get('id'))}, {'name': region_form.name.data,
                                                                       'type': region_form.type.data,
                                                                       'lat': region_form.lat.data,
                                                                       'lon': region_form.lon.data,
                                                                       'zoom': region_form.zoom.data,
                                                                       'body': save_region_bodies,
                                                                       'keyword': save_region_keywords})
    return redirect('/admin/regions')
  return render_template('admin_region_edit.html', region_form=region_form)

@app.route('/admin/bodies', methods=['GET', 'POST'])
@basic_auth.required
def admin_bodies():
  return render_template('admin_bodies.html', bodies=mongo.db.body.find())

@app.route('/admin/body/new', methods=['GET', 'POST'])
@basic_auth.required
def admin_body_new():
  if request.method == 'POST':
    body_form = BodyForm(request.form)
  else:
    body_form = BodyForm()
  if request.method == 'POST' and body_form.validate():
    new_body = json.loads(body_form.config.data)
    mongo.db.body.insert(new_body)
    return redirect('/admin/bodies')
  return render_template('admin_body_new.html', body_form=body_form)


@app.route('/admin/body/edit', methods=['GET', 'POST'])
@basic_auth.required
def admin_body_edit():
  if request.method == 'POST':
    body_form = BodyForm(request.form)
    body_form.config.data = json.dumps(json.loads(body_form.config.data), cls=util.MyEncoder, sort_keys=True, indent=2, ensure_ascii=False)
  else:
    config = []
    for value in mongo.db.body.find({'_id': ObjectId(request.args.get('id'))}):
      if '_id' in value:
        del value['_id']
      config.append(value)
    if len(config) == 1:
      config = config[0]
    else:
      abort(500)
    config = json.dumps(config, cls=util.MyEncoder, sort_keys=True, indent=2, ensure_ascii=False)
    body_form = BodyForm(config=config)
  if request.method == 'POST' and body_form.validate():
    updated_body = json.loads(body_form.config.data)
    if '_id' in updated_body:
      del updated_body['_id']
    mongo.db.body.update({'_id': ObjectId(request.args.get('id'))}, updated_body)
    return redirect('/admin/bodies')
  return render_template('admin_body_edit.html', body_form=body_form)


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


def generate_file_thumbnail_url(body_id, file_id, resulution, number):
    print file_id
    return "%s/%s/%s/%s/%s/%s/%s.jpg" % (app.config["thumbs_url"], body_id, str(file_id)[-1:], str(file_id)[-2:-1], file_id, resulution, number)
app.jinja_env.globals.update(generate_file_thumbnail_url=generate_file_thumbnail_url)

