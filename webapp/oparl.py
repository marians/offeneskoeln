# encoding: utf-8

"""
Copyright (c) 2012 Ernesto Ruge

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
from collections import OrderedDict

import werkzeug

from webapp import app

####################################################
# system
####################################################

@app.route('/oparl')
def oparl_general():
  return oparl_basic(lambda params: {
    "@id": "de.openruhr",
    "@type": "OParlSystem",
    "bodies": app.config['API_URL'] + "/oparl/body" + generate_postfix(params),
    "contact": {
        "email": "info@openruhr.de",
        "name": "Initiative OpenRuhr"
    }, 
    "info_url": "http://openruhr.de/",
    "name": "OpenRuhr Oparl Service",
    "new_objects": app.config['API_URL'] + "/feeds/new",
    "oparl_version": "http://oparl.org/spezifikation/1.0/",
    "product_url": "http://openruhr.de/",
    "removed_objects": app.config['API_URL'] + "/feeds/removed",
    "updated_objects": app.config['API_URL'] + "/feeds/updated",
    "vendor_url": "http://openruhr.de/"
  })


####################################################
# body
####################################################

# body list
@app.route('/oparl/body')
def oparl_bodies():
  return oparl_basic(oparl_bodies_data)

def oparl_bodies_data(params):
  return db.get_body(body_list=True, add_prefix=app.config['API_URL']+'/oparl/body/', add_postfix=generate_postfix(params))

# single body
@app.route('/oparl/body/<string:body_slug>')
def oparl_body(body_slug):
  return oparl_basic(oparl_body_data, params={'slug':body_slug})

def oparl_body_data(params):
  data = db.get_body(search_params={'title':params['slug']})
  if len(data) == 1:
    data[0]['committee'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/committee' + generate_postfix(params)
    data[0]['person'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/person' + generate_postfix(params)
    data[0]['meeting'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/meeting' + generate_postfix(params)
    data[0]['paper'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/paper' + generate_postfix(params)
    data[0]['document'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/document' + generate_postfix(params)
    data[0]['system'] = app.config['API_URL'] + '/oparl' + generate_postfix(params)
    data[0]['@type'] = 'OParlBody'
    data[0]['@id'] = data[0]['title']
    return data[0]
  elif len(data) == 0:
    abort(404)
  # Should never happen because slug is unique
  else:
    abort(500)

# body commitee list
@app.route('/oparl/body/<string:body_slug>/committee')
def oparl_body_committee(body_slug):
  return oparl_basic(oparl_body_committee_data, params={'body_slug':body_slug})

def oparl_body_committee_data(params):
  data = db.get_committee(committee_list=True, search_params={'body_slug':params['body_slug']}, add_prefix=app.config['API_URL']+'/oparl/committee/', add_postfix=generate_postfix(params))
  return data

# body person list
@app.route('/oparl/body/<string:body_slug>/person')
def oparl_body_person(body_slug):
  return oparl_basic(oparl_body_person_data, params={'body_slug':body_slug})

def oparl_body_person_data(params):
  data = db.get_person(person_list=True, search_params={'body_slug':params['body_slug']}, add_prefix=app.config['API_URL']+'/oparl/person/', add_postfix=generate_postfix(params))
  return data

# body meeting list
@app.route('/oparl/body/<string:body_slug>/meeting')
def oparl_body_meeting(body_slug):
  return oparl_basic(oparl_body_meeting_data, params={'body_slug':body_slug})

def oparl_body_meeting_data(params):
  data = db.get_meeting(meeting_list=True, search_params={'body_slug':params['body_slug']}, add_prefix=app.config['API_URL']+'/oparl/meeting/', add_postfix=generate_postfix(params))
  return data

# body paper list
@app.route('/oparl/body/<string:body_slug>/paper')
def oparl_body_paper(body_slug):
  return oparl_basic(oparl_body_paper_data, params={'body_slug':body_slug})

def oparl_body_paper_data(params):
  data = db.get_paper(paper_list=True, search_params={'body_slug':params['body_slug']}, add_prefix=app.config['API_URL']+'/oparl/paper/', add_postfix=generate_postfix(params))
  return data

# body document list
@app.route('/oparl/body/<string:body_slug>/document')
def oparl_body_document(body_slug):
  return oparl_basic(oparl_body_document_data, params={'body_slug':body_slug})

def oparl_body_document_data(params):
  data = db.get_document(document_list=True, search_params={'body_slug':params['body_slug']}, add_prefix=app.config['API_URL']+'/oparl/document/', add_postfix=generate_postfix(params))
  return data

####################################################
# committee
####################################################

# committee list
@app.route('/oparl/committee')
def oparl_committees():
  return oparl_basic(oparl_committees_data)

def oparl_committees_data(params):
  return db.get_committee(committee_list=True, add_prefix=app.config['API_URL']+'/oparl/committee/', add_postfix=generate_postfix(params))

# single committee
@app.route('/oparl/committee/<string:committee_slug>')
def oparl_committee(committee_slug):
  return oparl_basic(oparl_committee_data, params={'slug':committee_slug})

def oparl_committee_data(params):
  data = db.get_committee(search_params={'slug':params['slug']})
  if len(data) == 1:
    data[0]['body'] = app.config['API_URL'] + '/oparl/committee/' + params['slug'] + '/body' + generate_postfix(params)
    #TODO: data[0]['committee'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/committee' + generate_postfix(params)
    data[0]['person'] = app.config['API_URL'] + '/oparl/committee/' + params['slug'] + '/person' + generate_postfix(params)
    #TODO: data[0]['meeting'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/meeting' + generate_postfix(params)
    #TODO: data[0]['paper'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/paper' + generate_postfix(params)
    #TODO: data[0]['document'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/document' + generate_postfix(params)
    data[0]['@type'] = 'OParlCommittee'
    data[0]['@id'] = data[0]['identifier']
    return data[0]
  elif len(data) == 0:
    abort(404)
  # Should never happen because slug is unique
  else:
    abort(500)

# committee person list
@app.route('/oparl/committee/<string:committee_slug>/body')
def oparl_committee_body(committee_slug):
  return oparl_basic(oparl_committee_body_data, params={'committee_slug':committee_slug})

def oparl_committee_body_data(params):
  data = db.get_committee(deref={'value': 'body', 'list_select': 'title'}, search_params={'slug':params['committee_slug']}, add_prefix=app.config['API_URL']+'/oparl/body/', add_postfix=generate_postfix(params))
  return data

# committee person list
@app.route('/oparl/committee/<string:committee_slug>/person')
def oparl_committee_person(committee_slug):
  return oparl_basic(oparl_committee_person_data, params={'committee_slug':committee_slug})

def oparl_committee_person_data(params):
  data = db.get_person(person_list=True, search_params={'committee_slug':params['committee_slug']}, add_prefix=app.config['API_URL']+'/oparl/person/', add_postfix=generate_postfix(params))
  return data

####################################################
# person
####################################################

# person list
@app.route('/oparl/person')
def oparl_persons():
  return oparl_basic(oparl_person_data)

def oparl_persons_data(params):
  return db.get_person(person_list=True, add_prefix=app.config['API_URL']+'/oparl/person/', add_postfix=generate_postfix(params))

# single person
@app.route('/oparl/person/<string:person_slug>')
def oparl_person(person_slug):
  return oparl_basic(oparl_person_data, params={'slug':person_slug})

def oparl_person_data(params):
  data = db.get_person(search_params={'slug':params['slug']})
  if len(data) == 1:
    data[0]['body'] = app.config['API_URL'] + '/oparl/person/' + params['slug'] + '/body' + generate_postfix(params)
    data[0]['committee'] = app.config['API_URL'] + '/oparl/person/' + params['slug'] + '/committee' + generate_postfix(params)
    #TODO: data[0]['meeting'] = app.config['API_URL'] + '/oparl/body/' + params['slug'] + '/meeting' + generate_postfix(params)
    data[0]['@type'] = 'OParlPerson'
    data[0]['@id'] = data[0]['identifier']
    return data[0]
  elif len(data) == 0:
    abort(404)
  # Should never happen because slug is unique
  else:
    abort(500)

# person body list
@app.route('/oparl/person/<string:person_slug>/body')
def oparl_person_body(person_slug):
  return oparl_basic(oparl_person_body_data, params={'person_slug':person_slug})

def oparl_person_body_data(params):
  data = db.get_person(deref={'value': 'body', 'list_select': 'title'}, search_params={'slug':params['person_slug']}, add_prefix=app.config['API_URL']+'/oparl/body/', add_postfix=generate_postfix(params))
  return data

# person committee list
@app.route('/oparl/person/<string:person_slug>/committee')
def oparl_person_commiteee(person_slug):
  return oparl_basic(oparl_person_commitee_data, params={'person_slug':person_slug})

def oparl_person_commitee_data(params):
  data = db.get_person(deref={'value': 'committee', 'list_select': 'slug'}, search_params={'slug':params['person_slug']}, add_prefix=app.config['API_URL']+'/oparl/committee/', add_postfix=generate_postfix(params))
  return data

####################################################
# meeting
####################################################

# meeting list
@app.route('/oparl/meeting')
def oparl_meetings():
  return oparl_basic(oparl_meeting_data)

def oparl_meetings_data(params):
  return db.get_meeting(meeting_list=True, add_prefix=app.config['API_URL']+'/oparl/meeting/', add_postfix=generate_postfix(params))

# single meeting
@app.route('/oparl/meeting/<string:meeting_slug>')
def oparl_meeting(meeting_slug):
  return oparl_basic(oparl_meeting_data, params={'slug':meeting_slug})

def oparl_meeting_data(params):
  data = db.get_meeting(search_params={'slug':params['slug']})
  if len(data) == 1:
    data[0]['body'] = app.config['API_URL'] + '/oparl/meeting/' + params['slug'] + '/body' + generate_postfix(params)
    data[0]['meeting'] = app.config['API_URL'] + '/oparl/meeting/' + params['slug'] + '/meeting' + generate_postfix(params)
    data[0]['agendaitem'] = app.config['API_URL'] + '/oparl/meeting/' + params['slug'] + '/agendaitem' + generate_postfix(params)
    data[0]['document'] = app.config['API_URL'] + '/oparl/meeting/' + params['slug'] + '/document' + generate_postfix(params)
    data[0]['@type'] = 'OParlMeeting'
    data[0]['@id'] = data[0]['identifier']
    return data[0]
  elif len(data) == 0:
    abort(404)
  # Should never happen because slug is unique
  else:
    abort(500)

# meeting body list
@app.route('/oparl/meeting/<string:meeting_slug>/body')
def oparl_meeting_body(meeting_slug):
  return oparl_basic(oparl_meeting_body_data, params={'meeting_slug':meeting_slug})

def oparl_meeting_body_data(params):
  data = db.get_meeting(deref={'value': 'body', 'list_select': 'title'}, search_params={'slug':params['meeting_slug']}, add_prefix=app.config['API_URL']+'/oparl/body/', add_postfix=generate_postfix(params))
  return data

# meeting agendaitem list
@app.route('/oparl/meeting/<string:meeting_slug>/agendaitem')
def oparl_meeting_agendaitem(meeting_slug):
  return oparl_basic(oparl_meeting_agendaitem_data, params={'meeting_slug':meeting_slug})

def oparl_meeting_agendaitem_data(params):
  data = db.get_meeting(deref={'value': 'agendaitem', 'list_select': 'slug'}, search_params={'slug':params['meeting_slug']}, add_prefix=app.config['API_URL']+'/oparl/agendaitem/', add_postfix=generate_postfix(params))
  return data

# meeting document list
@app.route('/oparl/meeting/<string:meeting_slug>/document')
def oparl_meeting_document(meeting_slug):
  return oparl_basic(oparl_meeting_document_data, params={'meeting_slug':meeting_slug})

def oparl_meeting_document_data(params):
  data = db.get_meeting(deref={'value': 'document', 'list_select': 'slug'}, search_params={'slug':params['meeting_slug']}, add_prefix=app.config['API_URL']+'/oparl/document/', add_postfix=generate_postfix(params))
  return data

####################################################
# agendaitem
####################################################

# agendaitem list
@app.route('/oparl/agendaitems')
def oparl_agendaitems():
  return oparl_basic(oparl_agendaitems_data)

def oparl_agendaitems_data(params):
  return db.get_meeting(agendaitem_list=True, add_prefix=app.config['API_URL']+'/oparl/agendaitem/', add_postfix=generate_postfix(params))

# single agendaitem
@app.route('/oparl/agendaitem/<string:agendaitem_slug>')
def oparl_agendaitem(agendaitem_slug):
  return oparl_basic(oparl_agendaitem_data, params={'slug': agendaitem_slug})

def oparl_agendaitem_data(params):
  data = db.get_agendaitem(search_params={'slug':params['slug']})
  if len(data) == 1:
    data[0]['body'] = app.config['API_URL'] + '/oparl/agendaitem/' + params['slug'] + '/body' + generate_postfix(params)
    data[0]['meeting'] = app.config['API_URL'] + '/oparl/agendaitem/' + params['slug'] + '/meeting' + generate_postfix(params)
    data[0]['paper'] = app.config['API_URL'] + '/oparl/agendaitem/' + params['slug'] + '/paper' + generate_postfix(params)
    data[0]['@type'] = 'OParlAgendaitem'
    data[0]['@id'] = data[0]['identifier']
    return data[0]
  elif len(data) == 0:
    abort(404)
  # Should never happen because slug is unique
  else:
    abort(500)

# agendaitem body list
@app.route('/oparl/agendaitem/<string:agendaitem_slug>/body')
def oparl_agendaitem_body(agendaitem_slug):
  return oparl_basic(oparl_agendaitem_body_data, params={'agendaitem_slug':agendaitem_slug})

def oparl_agendaitem_body_data(params):
  data = db.get_agendaitem(deref={'value': 'body', 'list_select': 'title'}, search_params={'slug':params['agendaitem_slug']}, add_prefix=app.config['API_URL']+'/oparl/body/', add_postfix=generate_postfix(params))
  return data

# document meeting list
@app.route('/oparl/agendaitem/<string:agendaitem_slug>/meeting')
def oparl_agendaitem_meeting(agendaitem_slug):
  return oparl_basic(oparl_agendaitem_meeting_data, params={'agendaitem_slug':agendaitem_slug})

def oparl_agendaitem_meeting_data(params):
  data = db.get_meeting(meeting_list=True, search_params={'agendaitem_slug':params['agendaitem_slug']}, add_prefix=app.config['API_URL']+'/oparl/meeting/', add_postfix=generate_postfix(params))
  return data

# agendaitem paper list
@app.route('/oparl/agendaitem/<string:agendaitem_slug>/paper')
def oparl_agendaitem_paper(agendaitem_slug):
  return oparl_basic(oparl_agendaitem_paper_data, params={'agendaitem_slug':agendaitem_slug})

def oparl_agendaitem_paper_data(params):
  data = db.get_agendaitem(deref={'value': 'paper', 'list_select': 'slug'}, search_params={'slug':params['agendaitem_slug']}, add_prefix=app.config['API_URL']+'/oparl/paper/', add_postfix=generate_postfix(params))
  return data

####################################################
# paper
####################################################

# paper list
@app.route('/oparl/papers')
def oparl_papers():
  return oparl_basic(oparl_paper_data)

def oparl_papers_data(params):
  return db.get_paper(agendaitem_list=True, add_prefix=app.config['API_URL']+'/oparl/agendaitem/', add_postfix=generate_postfix(params))

# single paper
@app.route('/oparl/paper/<string:paper_slug>')
def oparl_paper(paper_slug):
  return oparl_basic(oparl_paper_data, params={'slug': paper_slug})

def oparl_paper_data(params):
  data = db.get_paper(search_params={'slug':params['slug']})
  if len(data) == 1:
    data[0]['body'] = app.config['API_URL'] + '/oparl/paper/' + params['slug'] + '/body' + generate_postfix(params)
    data[0]['agendaitem'] = app.config['API_URL'] + '/oparl/paper/' + params['slug'] + '/agendaitem' + generate_postfix(params)
    data[0]['paper'] = app.config['API_URL'] + '/oparl/paper/' + params['slug'] + '/paper' + generate_postfix(params) #TODO
    data[0]['document'] = app.config['API_URL'] + '/oparl/paper/' + params['slug'] + '/document' + generate_postfix(params)
    data[0]['@type'] = 'OParlPaper'
    data[0]['@id'] = data[0]['identifier']
    return data[0]
  elif len(data) == 0:
    abort(404)
  # Should never happen because slug is unique
  else:
    abort(500)

# paper body list
@app.route('/oparl/paper/<string:paper_slug>/body')
def oparl_paper_body(paper_slug):
  return oparl_basic(oparl_paper_body_data, params={'paper_slug':paper_slug})

def oparl_paper_body_data(params):
  data = db.get_paper(deref={'value': 'body', 'list_select': 'title'}, search_params={'slug':params['paper_slug']}, add_prefix=app.config['API_URL']+'/oparl/body/', add_postfix=generate_postfix(params))
  return data

# paper agendaitem list
@app.route('/oparl/paper/<string:paper_slug>/agendaitem')
def oparl_paper_agendaitem(paper_slug):
  return oparl_basic(oparl_paper_agendaitem_data, params={'paper_slug':paper_slug})

def oparl_paper_agendaitem_data(params):
  data = db.get_agendaitem(agendaitem_list=True, search_params={'paper_slug':params['paper_slug']}, add_prefix=app.config['API_URL']+'/oparl/agendaitem/', add_postfix=generate_postfix(params))
  return data

# paper document list
@app.route('/oparl/paper/<string:paper_slug>/document')
def oparl_paper_document(paper_slug):
  return oparl_basic(oparl_paper_document_data, params={'paper_slug':paper_slug})

def oparl_paper_document_data(params):
  data = db.get_paper(deref={'value': 'document', 'list_select': 'slug'}, search_params={'slug':params['paper_slug']}, add_prefix=app.config['API_URL']+'/oparl/document/', add_postfix=generate_postfix(params))
  return data

####################################################
# document
####################################################

# document list
@app.route('/oparl/documents')
def oparl_documents():
  return oparl_basic(oparl_documents_data)

def oparl_documents_data(params):
  return db.get_document(document_list=True, add_prefix=app.config['API_URL']+'/oparl/document/', add_postfix=generate_postfix(params))

# single paper
@app.route('/oparl/document/<string:document_slug>')
def oparl_document(document_slug):
  return oparl_basic(oparl_document_data, params={'slug': document_slug})

def oparl_document_data(params):
  data = db.get_document(search_params={'slug':params['slug']})
  if len(data) == 1:
    data[0]['body'] = app.config['API_URL'] + '/oparl/document/' + params['slug'] + '/body' + generate_postfix(params)
    data[0]['meeting'] = app.config['API_URL'] + '/oparl/document/' + params['slug'] + '/meeting' + generate_postfix(params)
    data[0]['paper'] = app.config['API_URL'] + '/oparl/document/' + params['slug'] + '/paper' + generate_postfix(params)
    data[0]['file'] = app.config['API_URL'] + '/oparl/document/' + params['slug'] + '/file'
    data[0]['@type'] = 'OParlPaper'
    data[0]['@id'] = data[0]['identifier']
    return data[0]
  elif len(data) == 0:
    abort(404)
  # Should never happen because slug is unique
  else:
    abort(500)

# document body list
@app.route('/oparl/document/<string:document_slug>/body')
def oparl_document_body(document_slug):
  return oparl_basic(oparl_document_body_data, params={'document_slug':document_slug})

def oparl_document_body_data(params):
  data = db.get_document(deref={'value': 'body', 'list_select': 'title'}, search_params={'slug':params['document_slug']}, add_prefix=app.config['API_URL']+'/oparl/body/', add_postfix=generate_postfix(params))
  return data

# document meeting list
@app.route('/oparl/document/<string:document_slug>/meeting')
def oparl_document_meeting(document_slug):
  return oparl_basic(oparl_document_meeting_data, params={'document_slug':document_slug})

def oparl_document_meeting_data(params):
  data = db.get_meeting(meeting_list=True, search_params={'document_slug':params['document_slug']}, add_prefix=app.config['API_URL']+'/oparl/meeting/', add_postfix=generate_postfix(params))
  return data

# document paper list
@app.route('/oparl/document/<string:document_slug>/paper')
def oparl_document_paper(document_slug):
  return oparl_basic(oparl_document_paper_data, params={'document_slug':document_slug})

def oparl_document_paper_data(params):
  data = db.get_paper(paper_list=True, search_params={'document_slug':params['document_slug']}, add_prefix=app.config['API_URL']+'/oparl/paper/', add_postfix=generate_postfix(params))
  return data


# document file
@app.route('/oparl/document/<string:document_slug>/file')
def oparl_document_file(document_slug):
  return oparl_basic(oparl_document_file_data, params={'document_slug':document_slug}, direct_output=True)

def oparl_document_file_data(params):
  document_data = db.get_document(search_params={'slug':params['document_slug']}, deref={'value': 'file'})

  if len(document_data) == 0:
    # TODO: Rendere informativere 404 Seite
    abort(404)
  document_data = document_data[0]
  # extension doesn't match file extension (avoiding arbitrary URLs)
  #proper_extension = attachment_info['filename'].split('.')[-1]
  #if proper_extension != extension:
  #    abort(404)

  # 'file' property is not set (e.g. due to depublication)
  if 'file' not in document_data:
    if 'depublication' in document_data:
      abort(410)  # Gone
    else:
      # TODO: log this as unexplicable...
      abort(500)

  # handle conditional GET
  #if 'If-Modified-Since' in request.headers:
  #  file_date = attachment_info['file']['uploadDate'].replace(tzinfo=None)
  #  request_date = util.parse_rfc1123date(request.headers['If-Modified-Since'])
  #  difference = file_date - request_date
  #  if difference < datetime.timedelta(0, 1):  # 1 second
  #    return Response(status=304)

  #if 'if-none-match' in request.headers:
  #    print "Conditional GET: If-None-Match"
  # TODO: handle ETag in request

  handler = db.get_file(document_data['file']['_id'])
  response = make_response(handler.read(), 200)
  response.mimetype = document_data['mimetype']
  response.headers['X-Robots-Tag'] = 'noarchive'
  response.headers['ETag'] = document_data['sha1_checksum']
  response.headers['Last-modified'] = util.rfc1123date(document_data['file']['uploadDate'])
  response.headers['Expires'] = util.expires_date(hours=(24 * 30))
  response.headers['Cache-Control'] = util.cache_max_age(hours=(24 * 30))
  response.headers['Content-Disposition'] = 'attachment; filename=' + document_data['filename']
  return response

####################################################
# misc
####################################################

def oparl_basic(content_fuction, params={}, direct_output=False):
  start_time = time.time()
  jsonp_callback = request.args.get('callback', None)
  request_info = {}
  html = request.args.get('html')
  html = html == '1'
  if html:
    request_info['html'] = 1
  extended_info = request.args.get('i')
  extended_info = extended_info == '1'
  if extended_info:
    request_info['i'] = 1
  # Singular Mode
  singular = request.args.get('s')
  singular = singular == '1'
  if singular:
    request_info['i'] = 1
  page = request.args.get('p')
  try:
    page = int(page)
  except (ValueError, TypeError):
    page = 1
  request_info['p'] = page
  
  ret = {
    'status': 0,
    'duration': int((time.time() - start_time) * 1000),
    'request': request_info,
    'response': {}
  }
  params.update(request_info)
  response = content_fuction(params)
  if not singular:
    convert_def = {'committee': 'committees', 'person': 'people', 'meeting': 'meetings', 'agendaitem': 'agendaitems', 'paper': 'papers', 'document': 'documents'}
    for key, value in convert_def.iteritems():
      if key in response:
        response[value] = response[key]
        del response[key]
  if direct_output:
    return response
  if extended_info:
    ret['response'] = response
  else:
    ret = response
  json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  if html:
    return render_template('oparl.html', data=json.JSONDecoder(object_pairs_hook=OrderedDict).decode(json_output))
  else:
    response = make_response(json_output, 200)
    response.mimetype = 'application/json'
    response.headers['Expires'] = util.expires_date(hours=24)
    response.headers['Cache-Control'] = util.cache_max_age(hours=24)
    return response


def generate_postfix(params):
  postfix = []
  if 'html' in params:
    postfix.append('html='+str(params['html']))
  if 'p' in params:
    if params['p'] > 1:
      postfix.append('p='+str(params['p']))
  if 'i' in params:
    postfix.append('i='+str(params['i']))
  if len(postfix):
    postfix = '?'+'&'.join(postfix)
  else:
    postfix = ''
  return(postfix)
  






# old stuff

@app.route("/oparl2/person/")
def oparl_documentsss():
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
  rs = util.get_rs()
  q = request.args.get('q', '*:*')
  fq = request.args.get('fq', '')
  sort = request.args.get('sort', 'score desc')
  start = int(request.args.get('start', '0'))
  numdocs = int(request.args.get('docs', '10'))
  date_param = request.args.get('date', '')
  get_attachments = 'attachments' in output
  get_thumbnails = 'thumbnails' in output and get_attachments
  get_consultations = 'consultations' in output
  get_facets = 'facets' in output
  #get_relations = 'relations' in output
  request_info = {}  # Info über die Anfrage
  query = False
  docs = False
  submission_ids = []
  # TODO: entscheiden, was mit get_relations passiert
  """
  Anhand der übergebenen Parameter wird entschieden, ob eine ES-Suche
  durchgeführt wird, oder ob die Abfrage direkt anhand von Kennungen
  (references) erfolgen kann.
  """
  
  if references is None:
    # Suche wird durchgeführt
    # (References-Liste via Suchmaschine füllen)
    query = db.query_submissions(rs=rs, q=q, fq=fq, sort=sort, start=start,
               docs=numdocs, date=date_param, facets=get_facets)
    if query['numhits'] > 0:
      submission_ids = [x['_id'] for x in query['result']]
    else:
      docs = []
  else:
    # Direkte Abfrage
    request_info = {
      'references': references
    }
  request_info['output'] = output

  # Abrufen der benötigten Dokumente aus der Datenbank
  if references is not None:
    docs = db.get_submissions(rs=rs, references=references,
            get_attachments=get_attachments,
            get_consultations=get_consultations,
            get_thumbnails=get_thumbnails)
  elif len(submission_ids) > 0:
    docs = db.get_submissions(rs=rs, submission_ids=submission_ids,
            get_attachments=get_attachments,
            get_consultations=get_consultations,
            get_thumbnails=get_thumbnails)

  ret = {
    'status': 0,
    'duration': int((time.time() - start_time) * 1000),
    'request': request_info,
    'response': {}
  }
  if docs:
    ret['response']['documents'] = docs
    ret['response']['numdocs'] = len(docs)
    if query and 'maxscore' in query:
      ret['response']['maxscore'] = query['maxscore']
    for n in range(len(docs)):
      docs[n]['reference'] = docs[n]['identifier']
      del docs[n]['identifier']

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


@app.route("/oparl2/locations")
def oparl_locations():
  start_time = time.time()
  jsonp_callback = request.args.get('callback', None)
  rs = util.get_rs()
  street = request.args.get('street', '')
  if street == '':
    abort(400)
  result = db.get_locations_by_name(rs, street)
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


@app.route("/oparl2/streets")
def oparl_streets():
  start_time = time.time()
  jsonp_callback = request.args.get('callback', None)
  rs = util.get_rs()
  if not rs:
    return
  lon = request.args.get('lon', '')
  lat = request.args.get('lat', '')
  radius = request.args.get('radius', '1000')
  if lat == '' or lon == '':
    abort(400)
  lon = float(lon)
  lat = float(lat)
  radius = int(radius)
  radius = min(radius, 500)
  result = db.get_locations(rs, lon, lat, radius)
  ret = {
    'status': 0,
    'duration': round((time.time() - start_time) * 1000),
    'request': {
      'rs': rs,
      'lon': lon,
      'lat': lat,
      'radius': radius
    },
    'response': result
  }
  try:
    json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
  except AttributeError:
    print >> sys.stderr, ret
    return null
  
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  response.headers['Expires'] = util.expires_date(hours=24)
  response.headers['Cache-Control'] = util.cache_max_age(hours=24)
  return response


# old: /api/session
@app.route("/oparl2/meeting")
def oparl_session():
  jsonp_callback = request.args.get('callback', None)
  location_entry = request.args.get('location_entry', '')
  lat = request.args.get('lat', '')
  lon = request.args.get('lon', '')
  region_id = request.args.get('region_id', '')
  if region_id != '':
    session['region_id'] = region_id
  if location_entry != '':
    session['location_entry'] = location_entry.encode('utf-8')
  if lat != '':
    session['lat'] = lat
  if lon != '':
    session['lon'] = request.args.get('lon', '')
  ret = {
    'status': 0,
    'response': {
      'location_entry': (session['location_entry'] if ('location_entry' in session) else None),
      'lat': (session['lat'] if ('lat' in session) else None),
      'lon': (session['lon'] if ('lon' in session) else None),
      'region_id': (session['region_id'] if ('region_id' in session) else 'xxxxxxxxxxxx'),
      'region': (app.config['RSMAP'][session['region_id']] if ('region_id' in session) else app.config['RSMAP']['xxxxxxxxxxxx'])
    }
  }
  json_output = json.dumps(ret, cls=util.MyEncoder, sort_keys=True)
  if jsonp_callback is not None:
    json_output = jsonp_callback + '(' + json_output + ')'
  response = make_response(json_output, 200)
  response.mimetype = 'application/json'
  return response


@app.route("/oparl2/response", methods=['POST'])
def oparl_response():
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
