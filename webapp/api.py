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
import sys

from flask import Flask
from flask import abort
from flask import render_template
from flask import make_response
from flask import request
from flask import session
from flask import redirect
from flask import Response

import werkzeug

from webapp import app, mongo


@app.route("/api/papers")
def api_papers():
  """
  API-Methode zur Suche von Dokumenten bzw. zum Abruf eines einzelnen
  Dokuments anhand einer Kennung (reference).
  Ist der URL-Parameter "reference" angegeben, handelt es sich um eine
  Dokumentenabfrage anhand der Kennung(en). Ansonsten ist es eine Suche.
  """
  start_time = time.time()
  jsonp_callback = request.args.get('callback', None)
  ref = request.args.get('reference', '')
  references = ref.split(',')
  if references == ['']:
    references = None
  output = request.args.get('output', '').split(',')
  q = request.args.get('q', '*:*')
  fq = request.args.get('fq', '')
  sort = request.args.get('sort', 'score:desc')
  start = int(request.args.get('start', '0'))
  papers_per_page = int(request.args.get('ppp', '10'))
  date_param = request.args.get('date', '')
  region = request.args.get('r', '')
  #get_consultations = 'consultations' in output
  get_facets = 'facets' in output
  #get_relations = 'relations' in output
  request_info = {}  # Info über die Anfrage
  query = False
  #docs = False
  paper_ids = []
  
  # Suche wird durchgeführt
  # (References-Liste via Suchmaschine füllen)
  query = db.query_paper(region=region, q=q, fq=fq, sort=sort, start=start,
             papers_per_page=papers_per_page, date=date_param, facets=get_facets)
  request_info['output'] = output

  ret = {
    'status': 0,
    'duration': int((time.time() - start_time) * 1000),
    'request': request_info,
    'response': query
  }
  
  #ret['response']['numhits'] = query['numhits']
  #ret['response']['data']
  #if get_facets and 'facets' in query:
  #  ret['response']['facets'] = query['facets']
    
  
  ret['response']['start'] = start
  ret['request']['sort'] = sort
  ret['request']['fq'] = fq

  json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  response.headers['Expires'] = util.expires_date(hours=24)
  response.headers['Cache-Control'] = util.cache_max_age(hours=24)
  return response


@app.route("/api/paper")
def api_paper():
  """
  API-Methode zur Suche von Dokumenten bzw. zum Abruf eines einzelnen
  Dokuments anhand einer Kennung (reference).
  Ist der URL-Parameter "reference" angegeben, handelt es sich um eine
  Dokumentenabfrage anhand der Kennung(en). Ansonsten ist es eine Suche.
  """
  start_time = time.time()
  jsonp_callback = request.args.get('callback', None)
  ref = request.args.get('reference', '')
  references = ref.split(',')
  if references == ['']:
    references = None
  output = request.args.get('output', '').split(',')
  q = request.args.get('q', '*:*')
  fq = request.args.get('fq', '')
  sort = request.args.get('sort', 'score desc')
  start = int(request.args.get('start', '0'))
  papers_per_page = int(request.args.get('ppp', '10'))
  date_param = request.args.get('date', '')
  region = request.args.get('r', '')
  #get_attachments = 'attachments' in output
  #get_thumbnails = 'thumbnails' in output and get_attachments
  #get_consultations = 'consultations' in output
  get_facets = 'facets' in output
  #get_relations = 'relations' in output
  request_info = {}  # Info über die Anfrage
  query = False
  #docs = False
  paper_ids = []
  # TODO: entscheiden, was mit get_relations passiert
  """
  Anhand der übergebenen Parameter wird entschieden, ob eine ES-Suche
  durchgeführt wird, oder ob die Abfrage direkt anhand von Kennungen
  (references) erfolgen kann.
  """
  
  if references is None:
    # Suche wird durchgeführt
    # (References-Liste via Suchmaschine füllen)
    query = db.query_paper(region=region, q=q, fq=fq, sort=sort, start=start,
               papers_per_page=papers_per_page, date=date_param, facets=get_facets)
    if query['numhits'] > 0:
      paper_ids = [x['_id'] for x in query['result']]
    else:
      paper_ids = []
  else:
    # Direkte Abfrage
    request_info = {
      'references': references
    }
  request_info['output'] = output

  ret = {
    'status': 0,
    'duration': int((time.time() - start_time) * 1000),
    'request': request_info,
    'response': {}
  }
  
  if query:
    ret['response']['numhits'] = query['numhits']
    if get_facets and 'facets' in query:
      ret['response']['facets'] = query['facets']
  
  ret['response']['start'] = start
  ret['request']['sort'] = sort
  ret['request']['fq'] = fq

  json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  response.headers['Expires'] = util.expires_date(hours=24)
  response.headers['Cache-Control'] = util.cache_max_age(hours=24)
  return response


@app.route("/api/locations")
def api_locations():
  start_time = time.time()
  jsonp_callback = request.args.get('callback', None)
  rs = util.get_rs()
  street = request.args.get('street', '')
  if street == '':
    abort(400)
  result = db.get_locations_by_name(street)
  ret = {
    'status': 0,
    'duration': round((time.time() - start_time) * 1000),
    'request': {
      'street': street
    },
    'response': result
  }
  json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  response.headers['Expires'] = util.expires_date(hours=24)
  response.headers['Cache-Control'] = util.cache_max_age(hours=24)
  return response


@app.route("/api/streets")
def api_streets():
  start_time = time.time()
  jsonp_callback = request.args.get('callback', None)
  lon = request.args.get('lon', '')
  lat = request.args.get('lat', '')
  region = request.args.get('region', app.config['region_default'])
  radius = request.args.get('radius', '1000')
  if lat == '' or lon == '':
    abort(400)
  lon = float(lon)
  lat = float(lat)
  radius = int(radius)
  radius = min(radius, 500)
  streets = db.get_locations(lon, lat, radius)
  result = {}
  # TODO: use msearch for getting paper num
  for street in streets:
    nodes = []
    for point in street['nodes']:
      nodes.append(point['location']['coordinates'])
    if street['name'] in result:
      result[street['name']]['nodes'].append(nodes)
    else:
      search_result = db.query_paper_num(region, street['name'])
      result[street['name']] = {
        'name': street['name'],
        'nodes': [ nodes ],
        'paper_count': search_result['num']
      }
      if 'name' in search_result:
        result[street['name']]['paper_name'] = search_result['name']
      if 'name' in search_result:
        result[street['name']]['paper_publishedDate'] = search_result['publishedDate']
  ret = {
    'status': 0,
    'duration': round((time.time() - start_time) * 1000),
    'request': {
      'lon': lon,
      'lat': lat,
      'radius': radius
    },
    'response': result
  }
  try:
    json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
  except AttributeError:
    return null
  
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  response.headers['Expires'] = util.expires_date(hours=24)
  response.headers['Cache-Control'] = util.cache_max_age(hours=24)
  return response


@app.route("/api/proxy/geocode")
def api_geocode():
  start = time.time()
  jsonp_callback = request.args.get('callback', None)
  address = request.args.get('address', '')
  region = request.args.get('region', '')
  if address == '':
    abort(400)
  obj = {
    'result': util.geocode(address, region)
  }
  obj['duration'] = int((time.time() - start) * 1000)
  json_output = json.dumps(obj, sort_keys=True)
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  response.headers['Expires'] = util.expires_date(hours=24)
  response.headers['Cache-Control'] = util.cache_max_age(hours=24)
  return response

@app.route('/api/regions')
def api_regions():
  jsonp_callback = request.args.get('callback', None)
  result = []
  regions=mongo.db.region.find()
  for region in regions:
    result.append({'id': region['_id'],
                   'type': region['type'],
                   'name': region['name'],
                   'lat': region['lat'],
                   'lon': region['lon'],
                   'zoom': region['zoom'],
                   'keyword': region['keyword']})
  json_output = json.dumps(result, cls=util.MyEncoder, sort_keys=True)
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  return response
  

@app.route("/api/session")
def api_session():
  jsonp_callback = request.args.get('callback', None)
  location_entry = request.args.get('location_entry', '')
  lat = request.args.get('lat', '')
  lon = request.args.get('lon', '')
  osm_id = request.args.get('osm_id', '')
  region_id = request.args.get('region_id', '')
  
  if location_entry != '':
    session['location_entry'] = location_entry.encode('utf-8')
  if lat != '':
    session['lat'] = lat
  if lon != '':
    session['lon'] = lon
  if osm_id != '':
    session['osm_id'] = osm_id
  if region_id != '':
    session['region_id'] = region_id
  ret = {
    'status': 0,
    'response': {
      'location_entry': (session['location_entry'] if ('location_entry' in session) else None),
      'lat': (session['lat'] if ('lat' in session) else None),
      'lon': (session['lon'] if ('lon' in session) else None),
      'osm_id': (session['osm_id'] if ('osm_id' in session) else None),
      'region_id': (session['region_id'] if ('region_id' in session) else None)
    }
  }
  json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  return response

""" TODO: make new
@app.route("/api/response", methods=['POST'])
def api_response():
  attachment_id = request.form['id']
  name = request.form['name']
  email = request.form['email']
  response_type = request.form['type']
  message = request.form['message']
  sent_on = request.form['sent_on']
  ip = str(request.remote_addr)
  db.add_response({'attachment_id': attachment_id, 'sent_on': sent_on, 'ip': ip, 'name': name, 'email': email, 'response_type': response_type, 'message': message})
  response = make_response('1', 200)
  response.mimetype = 'application/json'
  return response
"""