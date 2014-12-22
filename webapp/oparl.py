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
from bson import ObjectId, DBRef

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
    "bodies": "%s/oparl/body%s" % (app.config['api_url'], generate_postfix(params)),
    "contact": {
        "email": "info@openruhr.de",
        "name": "Initiative OpenRuhr"
    }, 
    "info_url": "http://openruhr.de/",
    "name": "OpenRuhr Oparl Service",
    "new_objects": "%s/feeds/new" % app.config['api_url'],
    "oparl_version": "http://oparl.org/spezifikation/1.0/",
    "product_url": "http://openruhr.de/",
    "removed_objects": "%s/feeds/removed" % app.config['api_url'],
    "updated_objects": "%s/feeds/updated" % app.config['api_url'],
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
  return db.get_body(body_list = True,
                     add_prefix = "%s/oparl/body/" % app.config['api_url'],
                     add_postfix=generate_postfix(params))

# single body
@app.route('/oparl/body/<string:body_id>')
def oparl_body(body_id):
  return oparl_basic(oparl_body_data, params={'_id': body_id})

def oparl_body_data(params):
  data = db.get_body(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['legislativeTerm'] = generate_sublist_url(params=params, main_type='body', sublist_type='legislativeTerm')
    data[0]['organization'] = generate_sublist_url(params=params, main_type='body', sublist_type='organization')
    data[0]['membership'] = generate_sublist_url(params=params, main_type='body', sublist_type='membership')
    data[0]['person'] = generate_sublist_url(params=params, main_type='body', sublist_type='person')
    data[0]['meeting'] = generate_sublist_url(params=params, main_type='body', sublist_type='meeting')
    data[0]['agendaItem'] = generate_sublist_url(params=params, main_type='body', sublist_type='agendaItem')
    data[0]['paper'] = generate_sublist_url(params=params, main_type='body', sublist_type='paper')
    data[0]['consultation'] = generate_sublist_url(params=params, main_type='body', sublist_type='consultation')
    data[0]['file'] = generate_sublist_url(params=params, main_type='body', sublist_type='file')
    data[0]['system'] = "%s/oparl%s" % (app.config['api_url'], generate_postfix(params))
    data[0]['@type'] = 'OParlBody'
    data[0]['@id'] = data[0]['_id']
    del data[0]['config']
    return data[0]
  elif len(data) == 0:
    abort(404)

# body legislativeTerm list
@app.route('/oparl/body/<string:body_id>/legislativeTerm')
def oparl_body_legislativeTerm(body_id):
  return oparl_basic(oparl_body_legislativeTerm_data,
                     params={'body_id':body_id})

def oparl_body_legislativeTerm_data(params):
  data = db.get_legislativeTerm(legislativeTerm_list = True,
                             search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                             add_prefix = "%s/oparl/legislativeTerm/" % app.config['api_url'],
                             add_postfix = generate_postfix(params))
  return data

# body organization list
@app.route('/oparl/body/<string:body_id>/organization')
def oparl_body_organization(body_id):
  return oparl_basic(oparl_body_organization_data,
                     params={'body_id':body_id})

def oparl_body_organization_data(params):
  data = db.get_organization(organization_list = True,
                             search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                             add_prefix = "%s/oparl/organization/" % app.config['api_url'],
                             add_postfix = generate_postfix(params))
  return data

# body membership list
@app.route('/oparl/body/<string:body_id>/membership')
def oparl_body_membership(body_id):
  return oparl_basic(oparl_body_membership_data,
                     params={'body_id': body_id})

def oparl_body_membership_data(params):
  data = db.get_membership(membership_list = True,
                       search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                       add_prefix = "%s/oparl/membership/" % app.config['api_url'],
                       add_postfix = generate_postfix(params))
  return data

# body person list
@app.route('/oparl/body/<string:body_id>/person')
def oparl_body_person(body_id):
  return oparl_basic(oparl_body_person_data,
                     params={'body_id': body_id})

def oparl_body_person_data(params):
  data = db.get_person(person_list = True,
                       search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                       add_prefix = "%s/oparl/person/" % app.config['api_url'],
                       add_postfix = generate_postfix(params))
  return data

# body meeting list
@app.route('/oparl/body/<string:body_id>/meeting')
def oparl_body_meeting(body_id):
  return oparl_basic(oparl_body_meeting_data,
                     params = {'body_id': body_id})

def oparl_body_meeting_data(params):
  data = db.get_meeting(meeting_list = True,
                        search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                        add_prefix = "%s/oparl/meeting/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  return data

# body agendaitem list
@app.route('/oparl/body/<string:body_id>/agendaItem')
def oparl_body_agendaItem(body_id):
  return oparl_basic(oparl_body_agendaItem_data,
                     params = {'body_id': body_id})

def oparl_body_agendaItem_data(params):
  data = db.get_agendaItem(agendaItem_list = True,
                        search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                        add_prefix = "%s/oparl/agendaItem/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  return data

# body consultation list
@app.route('/oparl/body/<string:body_id>/consultation')
def oparl_body_consultation(body_id):
  return oparl_basic(oparl_body_consultation_data,
                     params = {'body_id': body_id})

def oparl_body_consultation_data(params):
  data = db.get_consultation(consultation_list = True,
                        search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                        add_prefix = "%s/oparl/consultation/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  return data

# body paper list
@app.route('/oparl/body/<string:body_id>/paper')
def oparl_body_paper(body_id):
  return oparl_basic(oparl_body_paper_data,
                     params={'body_id': body_id})

def oparl_body_paper_data(params):
  data = db.get_paper(paper_list=True,
                      search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                      add_prefix =  "%s/oparl/paper/" % app.config['api_url'],
                      add_postfix = generate_postfix(params))
  return data

# body file list
@app.route('/oparl/body/<string:body_id>/file')
def oparl_body_file(body_id):
  return oparl_basic(oparl_body_file_data,
                     params={'body_id': body_id})

def oparl_body_file_data(params):
  data = db.get_file(file_list=True,
                     search_params = {'body': DBRef('body', ObjectId(params['body_id']))},
                     add_prefix = "%s/oparl/file/" % app.config['api_url'],
                     add_postfix = generate_postfix(params))
  return data

####################################################
# organization
####################################################

# organization list
@app.route('/oparl/organization')
def oparl_organizations():
  return oparl_basic(oparl_organizations_data)

def oparl_organizations_data(params):
  return db.get_organization(organization_list=True,
                             add_prefix = "%s/oparl/organization/" % app.config['api_url'],
                             add_postfix=generate_postfix(params))

# single organization
@app.route('/oparl/organization/<string:organization_id>')
def oparl_organization(organization_id):
  return oparl_basic(oparl_organization_data, params={'_id':organization_id})

def oparl_organization_data(params):
  data = db.get_organization(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['body'] = "%s/oparl/body/%s%s" % (app.config['api_url'], data[0]['body'].id, generate_postfix(params))
    data[0]['membership'] = generate_sublist_url(params=params, main_type='organization', sublist_type='membership')
    data[0]['meeting'] = generate_sublist_url(params=params, main_type='organization', sublist_type='meeting')
    data[0]['@type'] = 'OParlCommittee'
    data[0]['@id'] = data[0]['_id']
    return data[0]
  elif len(data) == 0:
    abort(404)

# organization membership list
@app.route('/oparl/organization/<string:organization_id>/membership')
def oparl_rganization_membership(organization_id):
  return oparl_basic(oparl_organization_membership_data, params={'organization_id': organization_id})

def oparl_organization_membership_data(params):
  data = db.get_membership(membership_list = True,
                           search_params = {'organization': DBRef('organization', ObjectId(params['organization_id']))},
                           add_prefix = "%s/oparl/membership/" % app.config['api_url'],
                           add_postfix = generate_postfix(params))
  return data

# organization meeting list
@app.route('/oparl/organization/<string:organization_id>/meeting')
def oparl_organization_meeting(organization_id):
  return oparl_basic(oparl_organization_meeting_data, params={'organization_id': organization_id})

def oparl_organization_meeting_data(params):
  data = db.get_meeting(meeting_list = True,
                        search_params = {'organization': DBRef('organization', ObjectId(params['organization_id']))},
                        add_prefix = "%s/oparl/meeting/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  return data

####################################################
# membership
####################################################

# membership list
@app.route('/oparl/membership')
def oparl_memberships():
  return oparl_basic(oparl_memberships_data)

def oparl_memberships_data(params):
  return db.get_membership(membership_list=True,
                           add_prefix = "%s/oparl/membership/" % app.config['api_url'],
                           add_postfix=generate_postfix(params))

# single organization
@app.route('/oparl/membership/<string:membership_id>')
def oparl_membership(membership_id):
  return oparl_basic(oparl_membership_data, params={'_id': membership_id})

def oparl_membership_data(params):
  data = db.get_membership(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['body'] = generate_single_url(params=params, type='body', id=data[0]['body'].id)
    data[0]['organization'] = generate_single_url(params=params, type='organization', id=data[0]['organization'].id)
    data[0]['person'] = generate_single_backref_url(params=params, get='get_person', type='person', reverse_type='membership', id=params['_id'])
    data[0]['@type'] = 'OParlMembership'
    data[0]['@id'] = data[0]['_id']
    return data[0]
  elif len(data) == 0:
    abort(404)

####################################################
# person
####################################################

# person list
@app.route('/oparl/person')
def oparl_persons():
  return oparl_basic(oparl_persons_data)

def oparl_persons_data(params):
  return db.get_person(person_list=True,
                       add_prefix = "%s/oparl/person/" % app.config['api_url'],
                       add_postfix=generate_postfix(params))

# single person
@app.route('/oparl/person/<string:person_id>')
def oparl_person(person_id):
  return oparl_basic(oparl_person_data, params={'_id': person_id})

def oparl_person_data(params):
  data = db.get_person(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['body'] = generate_single_url(params=params, type='body', id=data[0]['body'].id)
    data[0]['membership'] = generate_sublist_url(params=params, main_type='person', sublist_type='membership')
    data[0]['@type'] = 'OParlPerson'
    data[0]['@id'] = data[0]['_id']
    return data[0]
  elif len(data) == 0:
    abort(404)

# person membership list
@app.route('/oparl/person/<string:person_id>/membership')
def oparl_person_membership(person_id):
  return oparl_basic(oparl_person_membership_data, params={'person_id': person_id})

def oparl_person_membership_data(params):
  data = db.get_person(deref={'value': 'membership', 'list_select': '_id'},
                       search_params={'_id': ObjectId(params['person_id'])},
                       add_prefix = "%s/oparl/membership/" % app.config['api_url'],
                       add_postfix = generate_postfix(params))
  return data

####################################################
# meeting
####################################################

# meeting list
@app.route('/oparl/meeting')
def oparl_meetings():
  return oparl_basic(oparl_meetings_data)

def oparl_meetings_data(params):
  return db.get_meeting(meeting_list = True,
                        add_prefix = "%s/oparl/meeting/" % app.config['api_url'],
                        add_postfix=generate_postfix(params))

# single meeting
@app.route('/oparl/meeting/<string:meeting_id>')
def oparl_meeting(meeting_id):
  return oparl_basic(oparl_meeting_data, params={'_id': meeting_id})

def oparl_meeting_data(params):
  data = db.get_meeting(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['body'] = generate_single_url(params=params, type='body', id=data[0]['body'].id)
    data[0]['organization'] = generate_sublist_url(params=params, main_type='meeting', sublist_type='organization')
    data[0]['agendaItem'] = generate_sublist_url(params=params, main_type='meeting', sublist_type='agendaItem')
    data[0]['invitation'] = generate_sublist_url(params=params, main_type='meeting', sublist_type='invitation')
    if 'resultsProtocol' in data[0]:
      data[0]['resultsProtocol'] = generate_single_url(params=params, type='file', id=data[0]['resultsProtocol'].id)
    if 'verbatimProtocol' in data[0]:
      data[0]['verbatimProtocol'] = generate_single_url(params=params, type='file', id=data[0]['verbatimProtocol'].id)
    data[0]['auxiliaryFile'] = generate_sublist_url(params=params, main_type='meeting', sublist_type='auxiliaryFile')
    data[0]['@type'] = 'OParlMeeting'
    data[0]['@id'] = data[0]['_id']
    return data[0]
  elif len(data) == 0:
    abort(404)

# meeting organization list
@app.route('/oparl/meeting/<string:meeting_id>/organization')
def oparl_meeting_organization(meeting_id):
  return oparl_basic(oparl_meeting_organization_data, params={'meeting_id': meeting_id})

def oparl_meeting_organization_data(params):
  data = db.get_meeting(deref={'value': 'organization', 'list_select': '_id'},
                        search_params={'_id': ObjectId(params['meeting_id'])},
                        add_prefix = "%s/oparl/organization/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  return data

# meeting agendaItem list
@app.route('/oparl/meeting/<string:meeting_id>/agendaItem')
def oparl_meeting_agendaItem(meeting_id):
  return oparl_basic(oparl_meeting_agendaItem_data, params={'meeting_id': meeting_id})

def oparl_meeting_agendaItem_data(params):
  data = db.get_meeting(deref={'value': 'agendaItem', 'list_select': '_id'},
                        search_params={'_id': ObjectId(params['meeting_id'])},
                        add_prefix = "%s/oparl/agendaItem/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  return data

# meeting invitation list
@app.route('/oparl/meeting/<string:meeting_id>/invitation')
def oparl_meeting_invitation(meeting_id):
  return oparl_basic(oparl_meeting_invitation_data, params={'meeting_id': meeting_id})

def oparl_meeting_invitation_data(params):
  data = db.get_meeting(deref={'value': 'invitation', 'list_select': '_id'},
                        search_params={'_id': ObjectId(params['meeting_id'])},
                        add_prefix = "%s/oparl/file/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  return data

# meeting auxiliaryFile list
@app.route('/oparl/meeting/<string:meeting_id>/auxiliaryFile')
def oparl_meeting_auxiliaryFile(meeting_id):
  return oparl_basic(oparl_meeting_auxiliaryFile_data, params={'meeting_id': meeting_id})

def oparl_meeting_auxiliaryFile_data(params):
  data = db.get_meeting(deref={'value': 'auxiliaryFile', 'list_select': '_id'},
                        search_params={'_id': ObjectId(params['meeting_id'])},
                        add_prefix = "%s/oparl/file/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  return data

####################################################
# agendaItem
####################################################

# agendaItem list
@app.route('/oparl/agendaitem')
def oparl_agendaItems():
  return oparl_basic(oparl_agendaItems_data)

def oparl_agendaItems_data(params):
  return db.get_agendaItem(agendaItem_list = True,
                           add_prefix = "%s/oparl/agendaitem/" % app.config['api_url'],
                           add_postfix=generate_postfix(params))

# single agendaItem
@app.route('/oparl/agendaItem/<string:agendaItem_id>')
def oparl_agendaItem(agendaItem_id):
  return oparl_basic(oparl_agendaItem_data, params={'_id': agendaItem_id})

def oparl_agendaItem_data(params):
  data = db.get_agendaItem(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['body'] = generate_single_url(params=params, type='body', id=data[0]['body'].id)
    data[0]['meeting'] = generate_single_backref_url(params=params, get='get_meeting', type='meeting', reverse_type='agendaItem', id=params['_id'])
    data[0]['consultation'] = generate_single_url(params=params, type='consultation', id=data[0]['consultation'].id)
    data[0]['@type'] = 'OParlAgendaItem'
    data[0]['@id'] = data[0]['_id']
    return data[0]
  elif len(data) == 0:
    abort(404)

####################################################
# consultation
####################################################

# consultation list
@app.route('/oparl/consultation')
def oparl_consultations():
  return oparl_basic(oparl_consultations_data)

def oparl_consultations_data(params):
  return db.get_consultation(consultation_list = True,
                           add_prefix = "%s/oparl/consultation/" % app.config['api_url'],
                           add_postfix=generate_postfix(params))

# single consultation
@app.route('/oparl/consultation/<string:consultation_id>')
def oparl_consultation(consultation_id):
  return oparl_basic(oparl_consultation_data, params={'_id': consultation_id})

def oparl_consultation_data(params):
  data = db.get_consultation(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['body'] = generate_single_url(params=params, type='body', id=data[0]['body'].id)
    data[0]['agendaItem'] = generate_single_backref_url(params=params, get='get_agendaItem', type='agendaItem', reverse_type='consultation', id=params['_id'])
    data[0]['paper'] = generate_single_url(params=params, type='paper', id=data[0]['paper'].id)
    data[0]['organization'] = generate_sublist_url(params=params, main_type='consultation', sublist_type='organization')
    data[0]['@type'] = 'OParlConsultation'
    data[0]['@id'] = data[0]['_id']
    return data[0]
  elif len(data) == 0:
    abort(404)

# consultation organization list
@app.route('/oparl/consultation/<string:consultation_id>/organization')
def oparl_consultation_meeting(consultation_id):
  return oparl_basic(oparl_consultation_organization_data, params={'consultation_id': consultation_id})

def oparl_consultation_organization_data(params):
  data = db.get_consultation(deref={'value': 'organization', 'list_select': '_id'},
                             search_params={'_id': ObjectId(params['consultation_id'])},
                             add_prefix = "%s/oparl/organization/" % app.config['api_url'],
                             add_postfix = generate_postfix(params))
  return data


####################################################
# paper
####################################################

# paper list
@app.route('/oparl/paper')
def oparl_papers():
  return oparl_basic(oparl_papers_data)

def oparl_papers_data(params):
  return db.get_paper(paper_list = True,
                      add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                      add_postfix = generate_postfix(params))

# single paper
@app.route('/oparl/paper/<string:paper_id>')
def oparl_paper(paper_id):
  return oparl_basic(oparl_paper_data, params={'_id': paper_id})

def oparl_paper_data(params):
  data = db.get_paper(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['body'] = generate_single_url(params=params, type='body', id=data[0]['body'].id)
    data[0]['relatedPaper'] = generate_sublist_url(params=params, main_type='paper', sublist_type='relatedPaper')
    data[0]['superordinatedPaper'] = generate_sublist_url(params=params, main_type='paper', sublist_type='superordinatedPaper')
    data[0]['subordinatedPaper'] = generate_sublist_url(params=params, main_type='paper', sublist_type='subordinatedPaper')
    if 'mainFile' in data[0]:
      data[0]['mainFile'] = generate_single_url(params=params, type='file', id=data[0]['mainFile'].id)
    data[0]['auxiliaryFile'] = generate_sublist_url(params=params, main_type='paper', sublist_type='auxiliaryFile')
    #data[0]['originator'] = generate_sublist_url(params=params, main_type='file', sublist_type='paper') #TODO: BAEH - mixed organization + people
    data[0]['consultation'] = generate_sublist_url(params=params, main_type='paper', sublist_type='consultation')
    data[0]['underDirectionOf'] = generate_sublist_url(params=params, main_type='paper', sublist_type='underDirectionOf')
    data[0]['@type'] = 'OParlPaper'
    data[0]['@id'] = data[0]['_id']
    return data[0]
  elif len(data) == 0:
    abort(404)

# paper auxiliaryFile list
@app.route('/oparl/paper/<string:paper_id>/auxiliaryFile')
def oparl_paper_auxiliaryFile(paper_id):
  return oparl_basic(oparl_paper_auxiliaryFile_data, params={'paper_id': paper_id})

def oparl_paper_auxiliaryFile_data(params):
  data = db.get_paper(deref={'value': 'auxiliaryFile', 'list_select': '_id'},
                      search_params={'_id': ObjectId(params['paper_id'])},
                      add_prefix = "%s/oparl/file/" % app.config['api_url'],
                      add_postfix = generate_postfix(params))
  return data

# paper consultation list
@app.route('/oparl/paper/<string:paper_id>/consultation')
def oparl_paper_consultation(paper_id):
  return oparl_basic(oparl_paper_consultation_data, params={'paper_id': paper_id})

def oparl_paper_consultation_data(params):
  data = db.get_consultation(consultation_list = True,
                             search_params = {'paper': DBRef('paper', ObjectId(params['paper_id']))},
                             add_prefix = "%s/oparl/consultation/" % app.config['api_url'],
                             add_postfix = generate_postfix(params))
  return data

# paper relatedPaper list
@app.route('/oparl/paper/<string:paper_id>/relatedPaper')
def oparl_paper_relatedPaper(paper_id):
  return oparl_basic(oparl_paper_relatedPaper_data, params={'paper_id': paper_id})

def oparl_paper_relatedPaper_data(params):
  data_1 = db.get_paper(paper_list = True,
                        search_params = {'relatedPaper': DBRef('paper', ObjectId(params['paper_id']))},
                        add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  data_2 = db.get_paper(deref={'value': 'relatedPaper', 'list_select': '_id'},
                        search_params = {'_id': ObjectId(params['paper_id'])},
                        add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  data = data_1 + data_2
  return data

# paper subordinatedPaper list
@app.route('/oparl/paper/<string:paper_id>/subordinatedPaper')
def oparl_paper_subordinatedPaper(paper_id):
  return oparl_basic(oparl_paper_subordinatedPaper_data, params={'paper_id': paper_id})


def oparl_paper_subordinatedPaper_data(params):
  data_super = db.get_paper(paper_list = True,
                            search_params = {'superordinatedPaper': DBRef('paper', ObjectId(params['paper_id']))},
                            add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                            add_postfix = generate_postfix(params))
  data_sub = db.get_paper(deref = {'value': 'subordinatedPaper', 'list_select': '_id'},
                        search_params = {'_id': ObjectId(params['paper_id'])},
                        add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                        add_postfix = generate_postfix(params))
  print data_super + data_sub
  data = list(set(data_super + data_sub))
  return data

# paper superordinatedPaper list
@app.route('/oparl/paper/<string:paper_id>/superordinatedPaper')
def oparl_paper_superordinatedPaper(paper_id):
  return oparl_basic(oparl_paper_superordinatedPaper_data, params={'paper_id': paper_id})


def oparl_paper_superordinatedPaper_data(params):
  data_sub = db.get_paper(paper_list = True,
                          search_params = {'subordinatedPaper': DBRef('paper', ObjectId(params['paper_id']))},
                          add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                          add_postfix = generate_postfix(params))
  data_super = db.get_paper(deref = {'value': 'superordinatedPaper', 'list_select': '_id'},
                            search_params = {'_id': ObjectId(params['paper_id'])},
                            add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                            add_postfix = generate_postfix(params))
  data = list(set(data_super + data_sub))
  return data

# paper underDirectionOf list
@app.route('/oparl/paper/<string:paper_id>/underDirectionOf')
def oparl_paper_underDirectionOf(paper_id):
  return oparl_basic(oparl_paper_underDirectionOf_data, params={'paper_id': paper_id})

def oparl_paper_underDirectionOf_data(params):
  data = db.get_paper(deref={'value': 'underDirectionOf', 'list_select': '_id'},
                      search_params = {'_id': ObjectId(params['paper_id'])},
                      add_prefix = "%s/oparl/consultation/" % app.config['api_url'],
                      add_postfix = generate_postfix(params))
  return data


####################################################
# file
####################################################

# file list
@app.route('/oparl/file')
def oparl_files():
  return oparl_basic(oparl_files_data)

def oparl_files_data(params):
  return db.get_file(file_list = True,
                     add_prefix = "%s/oparl/file/" % app.config['api_url'],
                     add_postfix=generate_postfix(params))

# single file
@app.route('/oparl/file/<string:file_id>')
def oparl_document(file_id):
  return oparl_basic(oparl_file_data, params={'_id': file_id})

def oparl_file_data(params):
  data = db.get_file(search_params={'_id': ObjectId(params['_id'])})
  if len(data) == 1:
    data[0]['body'] = generate_single_url(params=params, type='body', id=data[0]['body'].id)
    data[0]['accessUrl'] = generate_sublist_url(params=params, main_type='file', sublist_type='accessUrl')
    data[0]['downloadUrl'] = generate_sublist_url(params=params, main_type='file', sublist_type='downloadUrl')
    data[0]['meeting'] = generate_sublist_url(params=params, main_type='file', sublist_type='meeting')
    data[0]['paper'] = generate_sublist_url(params=params, main_type='file', sublist_type='paper')
    if 'masterFile' in data[0]:
      data[0]['masterFile'] = generate_single_url(params=params, type='file', id=data[0]['mainFile'].id)
    data[0]['derivativeFile'] = generate_sublist_url(params=params, main_type='file', sublist_type='derivativeFile')
    data[0]['@type'] = 'OParlPaper'
    data[0]['@id'] = data[0]['_id']
    if 'file' in data[0]:
      del data[0]['file']
    return data[0]
  elif len(data) == 0:
    abort(404)

# file meeting list
@app.route('/oparl/file/<string:file_id>/meeting')
def oparl_file_meeting(file_id):
  return oparl_basic(oparl_file_meeting_data, params={'file_id': file_id})

def oparl_file_meeting_data(params):
  invitation_data = db.get_meeting(meeting_list = True,
                                   search_params = {'invitation': DBRef('file', ObjectId(params['file_id']))},
                                   add_prefix = "%s/oparl/meeting/" % app.config['api_url'],
                                   add_postfix = generate_postfix(params))
  auxiliaryFile_data = db.get_meeting(meeting_list = True,
                                      search_params = {'auxiliaryFile': DBRef('file', ObjectId(params['file_id']))},
                                      add_prefix = "%s/oparl/meeting/" % app.config['api_url'],
                                      add_postfix = generate_postfix(params))
  resultsProtocol_data = db.get_meeting(meeting_list = True,
                                        search_params = {'resultsProtocol': DBRef('file', ObjectId(params['file_id']))},
                                        add_prefix = "%s/oparl/meeting/" % app.config['api_url'],
                                        add_postfix = generate_postfix(params))
  verbatimProtocol_data = db.get_meeting(meeting_list = True,
                                        search_params = {'verbatimProtocol': DBRef('file', ObjectId(params['file_id']))},
                                        add_prefix = "%s/oparl/meeting/" % app.config['api_url'],
                                        add_postfix = generate_postfix(params))
  data = invitation_data + auxiliaryFile_data + resultsProtocol_data + verbatimProtocol_data
  return data

# file paper list
@app.route('/oparl/file/<string:file_id>/paper')
def oparl_file_paper(file_id):
  return oparl_basic(oparl_file_paper_data, params={'file_id': file_id})

def oparl_file_paper_data(params):
  mainFile_data = db.get_paper(paper_list = True,
                               search_params = {'mainFile': DBRef('file', ObjectId(params['file_id']))},
                               add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                               add_postfix = generate_postfix(params))
  auxiliaryFile_data = db.get_paper(paper_list = True,
                                    search_params = {'auxiliaryFile': DBRef('file', ObjectId(params['file_id']))},
                                    add_prefix = "%s/oparl/paper/" % app.config['api_url'],
                                    add_postfix = generate_postfix(params))
  data = mainFile_data + auxiliaryFile_data
  return data

# file accessUrl
@app.route('/oparl/file/<string:file_id>/accessUrl')
def oparl_file_accessUrl(file_id):
  return oparl_basic(oparl_file_accessUrl_data, params={'file_id': file_id}, direct_output=True)

def oparl_file_accessUrl_data(params):
  file_data = db.get_file(deref={'values': ['file']},
                              search_params={'_id': ObjectId(params['file_id'])})

  if len(file_data) == 0:
    # TODO: Rendere informativere 404 Seite
    abort(404)
  file_data = file_data[0]
  # extension doesn't match file extension (avoiding arbitrary URLs)
  #proper_extension = attachment_info['filename'].split('.')[-1]
  #if proper_extension != extension:
  #    abort(404)

  # 'file' property is not set (e.g. due to depublication)
  if 'file' not in file_data:
    if 'depublication' in file_data:
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

  handler = db.get_file_data(file_data['file']['_id'])
  response = make_response(handler.read(), 200)
  response.mimetype = file_data['mimetype']
  response.headers['X-Robots-Tag'] = 'noarchive'
  response.headers['ETag'] = file_data['sha1Checksum']
  response.headers['Last-modified'] = util.rfc1123date(file_data['file']['uploadDate'])
  response.headers['Expires'] = util.expires_date(hours=(24 * 30))
  response.headers['Cache-Control'] = util.cache_max_age(hours=(24 * 30))
  return response


# file downloadUrl
@app.route('/oparl/file/<string:file_id>/downloadUrl')
def oparl_file_downloadUrl(file_id):
  return oparl_basic(oparl_file_downloadUrl_data, params={'file_id': file_id}, direct_output=True)

def oparl_file_downloadUrl_data(params):
  file_data = db.get_file(deref={'values': ['file']},
                          search_params={'_id': ObjectId(params['file_id'])})

  if len(file_data) == 0:
    # TODO: Rendere informativere 404 Seite
    abort(404)
  file_data = file_data[0]
  
  # 'file' property is not set (e.g. due to depublication)
  if 'file' not in file_data:
    if 'depublication' in file_data:
      abort(410)  # Gone
    else:
      # TODO: log this as unexplicable...
      abort(500)

  handler = db.get_file_data(file_data['file']['_id'])
  response = make_response(handler.read(), 200)
  response.mimetype = file_data['mimetype']
  response.headers['X-Robots-Tag'] = 'noarchive'
  response.headers['ETag'] = file_data['sha1Checksum']
  response.headers['Last-modified'] = util.rfc1123date(file_data['file']['uploadDate'])
  response.headers['Expires'] = util.expires_date(hours=(24 * 30))
  response.headers['Cache-Control'] = util.cache_max_age(hours=(24 * 30))
  response.headers['Content-Disposition'] = 'attachment; filename=' + file_data['filename']
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
    response.headers['Access-Control-Allow-Origin'] = '*'
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
  

def generate_sublist_url(params={}, main_type='', main_id='_id', sublist_type=''):
  return "%s/oparl/%s/%s/%s%s" % (app.config['api_url'], main_type, params[main_id], sublist_type, generate_postfix(params))

def generate_single_url(params={}, type='', id=''):
  return "%s/oparl/%s/%s%s" % (app.config['api_url'], type, id, generate_postfix(params))

def generate_single_backref_url(params={}, get='', type='', reverse_type='', id=''):
  get = getattr(db, get)
  uid = str((get(search_params={reverse_type: DBRef(reverse_type, ObjectId(id))}, values={'_id':1}))[0]['_id'])
  return "%s/oparl/%s/%s%s" % (app.config['api_url'], type, uid, generate_postfix(params))


#"%s/oparl/body/%s/organization%s" % (app.config['api_url'], params['_id'], generate_postfix(params))



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
      'region': (app.app.config['RSMAP'][session['region_id']] if ('region_id' in session) else app.app.config['RSMAP']['xxxxxxxxxxxx'])
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
