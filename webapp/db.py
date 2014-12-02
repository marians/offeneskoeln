# encoding: utf-8

from webapp import mongo, app
import pyes
import util

from bson import ObjectId, DBRef
import gridfs

import pprint
import urllib2
import datetime
import dateutil.relativedelta

from flask import abort

def get_config(body_uid=False):
  """
  Returns Config JSON
  """
  config = mongo.db.config.find_one()
  if '_id' in config:
    del config['_id']
  if body_uid:
    local_config = mongo.db.body.find_one({'_id': ObjectId(body_uid)})
    if 'config' in local_config:
      config = merge_dict(config, local_config['config'])
      del local_config['config']
    config['city'] = local_config
  return config

def merge_dict(self, x, y):
  merged = dict(x,**y)
  xkeys = x.keys()
  for key in xkeys:
    if type(x[key]) is types.DictType and y.has_key(key):
      merged[key] = merge_dict(x[key],y[key])
  return merged

def get_body(body_list=False, add_prefix='', add_postfix='', search_params={}):
  result = []
  if body_list:
    for body in mongo.db.body.find(search_params,{'_id':1}):
      result.append("%s%s%s" % (add_prefix, body['_id'], add_postfix))
  else:
    for body in mongo.db.body.find(search_params):
      result.append(body)
  return result

def get_legislativeTerm(legislativeTerm_list=False, add_prefix='', add_postfix='', search_params={}, deref={}):
  result = []
  if legislativeTerm_list:
    for legislativeTerm in mongo.db.legislativeTerm.find(search_params,{'_id':1}):
      result.append(add_prefix + str(legislativeTerm['_id']) + add_postfix)
  else:
    for legislativeTerm in mongo.db.legislativeTerm.find(search_params):
      result.append(legislativeTerm)
  return dereference_result_items(result, deref, add_prefix, add_postfix)


def get_organization(organization_list=False, add_prefix='', add_postfix='', search_params={}, deref={}):
  result = []
  #search_params = dereference_search_params(search_params, [
  #  {'from': 'body_id', 'to': 'body', 'field': '_id', 'get_function': get_body},
  #  {'from': 'person_id', 'to': 'person', 'field': '_id', 'get_function': get_person}
  #])
  if organization_list:
    for organization in mongo.db.organization.find(search_params,{'_id':1}):
      result.append(add_prefix + str(organization['_id']) + add_postfix)
  else:
    for organization in mongo.db.organization.find(search_params):
      result.append(organization)
  return dereference_result_items(result, deref, add_prefix, add_postfix)

def get_membership(membership_list=False, add_prefix='', add_postfix='', search_params={}, deref={}):
  result = []
  if membership_list:
    for membership in mongo.db.membership.find(search_params,{'_id':1}):
      result.append(add_prefix + str(membership['_id']) + add_postfix)
  else:
    for membership in mongo.db.membership.find(search_params):
      result.append(membership)
  return dereference_result_items(result, deref, add_prefix, add_postfix)

def get_person(person_list=False, add_prefix='', add_postfix='', search_params={}, deref={}, values={}):
  result = []
  #search_params = dereference_search_params(search_params, [
  #  {'from': 'body_slug', 'to': 'body', 'field': 'title', 'get_function': get_body},
  #  {'from': 'committee_slug', 'to': 'committee', 'field': 'slug', 'get_function': get_committee}
  #])
  if person_list:
    for person in mongo.db.person.find(search_params,{'_id':1}):
      result.append(add_prefix + str(person['_id']) + add_postfix)
  else:
    if len(values):
      for person in mongo.db.person.find(search_params, values):
        result.append(person)
    else:
      for person in mongo.db.person.find(search_params):
        result.append(person)
  return dereference_result_items(result, deref, add_prefix, add_postfix)

def get_meeting(meeting_list=False, add_prefix='', add_postfix='', search_params={}, deref={}, values={}):
  result = []
  #search_params = dereference_search_params(search_params, [
  #  {'from': 'body_slug', 'to': 'body', 'field': 'title', 'get_function': get_body},
  #  {'from': 'committee_slug', 'to': 'committee', 'field': 'slug', 'get_function': get_committee},
  #  {'from': 'agendaitem_slug', 'to': 'agendaitem', 'field': 'slug', 'get_function': get_agendaitem},
  #  {'from': 'document_slug', 'to': 'document', 'field': 'slug', 'get_function': get_document}
  #])
  if meeting_list:
    for meeting in mongo.db.meeting.find(search_params,{'_id':1}):
      result.append(add_prefix + str(meeting['_id']) + add_postfix)
  else:
    if len(values):
      for meeting in mongo.db.meeting.find(search_params, values):
        result.append(meeting)
    else:
      for meeting in mongo.db.meeting.find(search_params):
        result.append(meeting)
  return dereference_result_items(result, deref, add_prefix, add_postfix)

def get_agendaItem(agendaItem_list=False, add_prefix='', add_postfix='', search_params={}, deref={}, values={}):
  result = []
  #search_params = dereference_search_params(search_params, [
  #  {'from': 'body_slug', 'to': 'body', 'field': 'title', 'get_function': get_body},
  #  {'from': 'paper_slug', 'to': 'paper', 'field': 'slug', 'get_function': get_paper}
  #])
  if agendaItem_list:
    for agendaitem in mongo.db.agendaitem.find(search_params,{'_id':1}):
      result.append(add_prefix + str(agendaitem['_id']) + add_postfix)
  else:
    if len(values):
      for agendaitem in mongo.db.agendaitem.find(search_params, values):
        result.append(agendaitem)
    else:
      for agendaitem in mongo.db.agendaitem.find(search_params):
        result.append(agendaitem)
  return dereference_result_items(result, deref, add_prefix, add_postfix)

def get_consultation(consultation_list=False, add_prefix='', add_postfix='', search_params={}, deref={}):
  result = []
  #search_params = dereference_search_params(search_params, [
  #  {'from': 'body_slug', 'to': 'body', 'field': 'title', 'get_function': get_body},
  #  {'from': 'document_slug', 'to': 'document', 'field': 'slug', 'get_function': get_document}
  #])
  if consultation_list:
    for consultation in mongo.db.consultation.find(search_params,{'_id':1}):
      result.append(add_prefix + str(consultation['_id']) + add_postfix)
  else:
    for consultation in mongo.db.consultation.find(search_params):
      result.append(consultation)
  return dereference_result_items(result, deref, add_prefix, add_postfix)

def get_paper(paper_list=False, add_prefix='', add_postfix='', search_params={}, deref={}):
  result = []
  #search_params = dereference_search_params(search_params, [
  #  {'from': 'body_slug', 'to': 'body', 'field': 'title', 'get_function': get_body},
  #  {'from': 'document_slug', 'to': 'document', 'field': 'slug', 'get_function': get_document}
  #])
  if paper_list:
    for paper in mongo.db.paper.find(search_params,{'_id':1}):
      result.append(add_prefix + str(paper['_id']) + add_postfix)
  else:
    for paper in mongo.db.paper.find(search_params):
      result.append(paper)
  return dereference_result_items(result, deref, add_prefix, add_postfix)

def get_file(file_list=False, add_prefix='', add_postfix='', search_params={}, deref={}):
  result = []
  #search_params = dereference_search_params(search_params, [
  #  {'from': 'body_slug', 'to': 'body', 'field': 'title', 'get_function': get_body}
  #])
  if file_list:
    for file in mongo.db.file.find(search_params,{'_id':1}):
      result.append(add_prefix + str(file['_id']) + add_postfix)
  else:
    for file in mongo.db.file.find(search_params):
      result.append(file)
  return dereference_result_items(result, deref, add_prefix, add_postfix)


def get_file_data(file_id):
  """Return the actual file info"""
  fs = gridfs.GridFS(mongo.db)
  return fs.get(file_id)

def dereference_search_params(search_params, to_dereference):
  for key in to_dereference:
    if key['from'] in search_params:
      print key['get_function']
      search_params[key['to']] = key['get_function'](search_params={key['field']: ObjectId(search_params[key['from']]) if key['field'] == '_id' else search_params[key['from']]})
      print search_params[key['to']]
      if len(search_params[key['to']]) == 1:
        search_params[key['to']] = DBRef(key['to'], search_params[key['to']][0]['_id'])
        del search_params[key['from']]
      elif len(search_params['body']) == 0:
        abort(404)
      else:
        abort(500)
  return search_params

def dereference_result_items(result, deref, add_prefix, add_postfix):
  if deref:
    if len(result) == 1:
      if deref['value'] in result[0]:
        # Single DBRef
        if isinstance(result[0][deref['value']], DBRef):
          if 'list_select' in deref:
            if deref['list_select'] == '_id':
              result[0][deref['value']] = "%s%s%s" % (add_prefix, result[0][deref['value']].id, add_postfix)
            else:
              result[0][deref['value']] = "%s%s%s" % (add_prefix, mongo.db.dereference(result[0][deref['value']])[deref['list_select']], add_postfix)
          else:
            result[0][deref['value']] = mongo.db.dereference(result[0][deref['value']])
          return result
        # DBRef List
        else:
          for item_id in range(len(result[0][deref['value']])):
            if 'list_select' in deref:
              if deref['list_select'] == '_id':
                result[0][deref['value']][item_id] = "%s%s%s" % (add_prefix, result[0][deref['value']][item_id].id, add_postfix)
              else:
                result[0][deref['value']][item_id] = "%s%s%s" % (add_prefix, mongo.db.dereference(result[0][deref['value']][item_id])[deref['list_select']], add_postfix)
            else:
              result[0][deref['value']][item_id] = mongo.db.dereference(result[0][deref['value']][item_id])
          return result[0][deref['value']]
      else:
        return []
    # makes no sense
    else:
      abort(500)
  else:
    return result
  return result


def get_attachment(attachment_id, include_file_meta=True):
  """Return metadata about the attachment (and the file)"""
  if type(attachment_id) in [str, unicode]:
    attachment_id = ObjectId(attachment_id)
  attachment = mongo.db.attachments.find_one({'_id': attachment_id})
  if attachment is None:
    return None
  if include_file_meta:
    if 'file' in attachment:
      file_info = mongo.db.fs.files.find_one({
        '_id': attachment['file'].id
      })
      attachment['file'] = file_info
  return attachment




def get_submissions(rs=None, references=None, submission_ids=None, get_attachments=False,
          get_consultations=False, get_thumbnails=False):
  """
  Liefert die in der Liste references identifizierten
  Drucksachen zurück

  # TODO: Eventuell ist ein OR-Query schneller als n Abfragen nach Einzelobjekten?
  """
  mode = None
  keys = []
  if references is None and submission_ids is None:
    raise ValueError('Neither references nor submission_ids given.')
  elif references is not None:
    mode = 'references'
    if type(references) is not list or references == []:
      raise ValueError('Need reference to be a list of strings.')
    keys = references
  elif submission_ids is not None:
    mode = 'submission_ids'
    if type(submission_ids) is not list or submission_ids == []:
      raise ValueError('Need submission_ids to be a list of strings or ObjectIds.')
    keys = submission_ids
  submissions = []
  for r in keys:
    query = None
    if mode == 'references':
      query = {'urls': r, 'rs': rs }
    else:
      if type(r) != ObjectId:
        r = ObjectId(r)
      query = {'_id': r, "rs" : rs}
    result = mongo.db.submissions.find(query)
    for res in result:
      if 'urls' in res and len(res['urls']):
        res['url'] = util.submission_url(res['urls'][0])
      else:
        res['url'] = util.submission_url(res['identifier'])
      if get_attachments:
        # Zugehörige attachments einfügen
        if 'attachments' in res:
          for n in range(len(res['attachments'])):
            a = res['attachments'][n]
            res['attachments'][n] = mongo.db.attachments.find_one({'_id': a.id})
            if 'depublication' not in res['attachments'][n]:
              res['attachments'][n]['url'] = util.attachment_url(a.id, filename=res['attachments'][n]['filename'])
            if not get_thumbnails:
              if 'thumbnails' in res['attachments'][n]:
                del res['attachments'][n]['thumbnails']
            else:
              if 'thumbnails' in res['attachments'][n]:
                for height in res['attachments'][n]['thumbnails'].keys():
                  for t in range(len(res['attachments'][n]['thumbnails'][height])):
                    res['attachments'][n]['thumbnails'][height][t]['url'] = util.thumbnail_url(
                        attachment_id=res['attachments'][n]['_id'], size=height,
                        page=res['attachments'][n]['thumbnails'][height][t]['page'])
                  res['attachments'][n]['thumbnails'][height] = sorted(res['attachments'][n]['thumbnails'][height], key=lambda x: x.get('page', -1))
      if get_consultations:
        # Verweisende agendaitems finden
        sessions = mongo.db.sessions.find({'agendaitems.submissions.$id': res['_id'], "rs" : rs})
        if sessions.count() > 0:
          res['consultations'] = []
          for session in sessions:
            relevant_agendaitems = []
            for a in session['agendaitems']:
              if 'submissions' not in a:
                continue
              for subm in a['submissions']:
                if subm.id == res['_id']:
                  del a['submissions']
                  relevant_agendaitems.append(a)
            session['agendaitems'] = relevant_agendaitems
            # und wiederum Attachments auflösen
            if get_attachments and 'attachments' in session:
              for n in range(len(session['attachments'])):
                a = session['attachments'][n]
                session['attachments'][n] = mongo.db.attachments.find_one(a.id)
                if 'depublication' not in session['attachments'][n]:
                  session['attachments'][n]['url'] = util.attachment_url(a.id, filename=session['attachments'][n]['filename'])
                if get_thumbnails == False and 'thumbnails' in session['attachments'][n]:
                  del session['attachments'][n]['thumbnails']
                else:
                  if 'thumbnails' in session['attachments'][n]:
                    for height in session['attachments'][n]['thumbnails'].keys():
                      for t in range(len(session['attachments'][n]['thumbnails'][height])):
                        session['attachments'][n]['thumbnails'][height][t]['url'] = util.thumbnail_url(
                            attachment_id=session['attachments'][n]['_id'], size=height,
                            page=session['attachments'][n]['thumbnails'][height][t]['page'])
            res['consultations'].append(session)
      submissions.append(res)
  return submissions


def query_submissions(rs=None, q='', fq=None, sort='score desc', start=0, docs=10, date=None, facets=None):
  (sort_field, sort_order) = sort.split(' ')
  if sort_field == 'score':
    sort_field = '_score'
  sort = {sort_field: {'order': sort_order}}
  query = pyes.query.BoolQuery()
  query.add_must(pyes.StringQuery(q, default_operator="AND"))
  rest = True
  x = 0
  result = []
  while rest:
    y = fq.find(":", x)
    if y == -1:
      break
    temp = fq[x:y]
    x = y + 1
    if fq[x:x+5] == "&#34;":
      y = fq.find("&#34;", x+5)
      if y == -1:
        break
      result.append((temp, fq[x+5:y]))
      x = y + 6
      if x > len(fq):
        break
    else:
      y = fq.find(";", x)
      if y == -1:
        result.append((temp, fq[x:len(fq)]))
        break
      else:
        result.append((temp, fq[x:y]))
        x = y + 1
  for sfq in result:
    if sfq[0] == 'date':
      (year, month) = sfq[1].split('-')
      date_start = datetime.datetime(int(year), int(month), 1)
      date_end = date_start + dateutil.relativedelta.relativedelta(months=+1,seconds=-1)
      query.add_must(pyes.RangeQuery(qrange=pyes.ESRange('date',date_start, date_end)))
    else:
      query.add_must(pyes.TermQuery(field=sfq[0], value=sfq[1]))
  search = pyes.query.Search(query=query, fields=[''], start=start, size=docs, sort=sort)
  search.facet.add_term_facet('type')
  search.facet.add_term_facet('rs')
  search.facet.add_term_facet('committee')
  search.facet.add_date_facet(field='date', name='date', interval='month')
  es = pyes.ES(app.config['ES_HOST']+':'+str(app.config['ES_PORT']))
  es.default_indices = [app.config['ES_INDEX_NAME_PREFIX']+'-latest']
  es.refresh()
  result = es.search(search, model=lambda x, y: y)
  ret = {
    'numhits': result.total,
    'maxscore': result.max_score,
    'result': [],
    'facets': {}
  }
  if result.max_score is not None:
    ret['maxscore'] = result.max_score
  for key in result.facets:
    ret['facets'][key] = {}
    if result.facets[key]['_type'] == 'date_histogram':
      for subval in result.facets[key]['entries']:
        ret['facets'][key][datetime.datetime.fromtimestamp(int(subval['time'])/1000).strftime('%Y-%m')] = subval['count']
    if result.facets[key]['_type'] == 'terms':
      for subval in result.facets[key]['terms']:
        ret['facets'][key][subval['term']] = subval['count']
  for r in result:
    ret['result'].append({
      '_id': str(r['_id']),
      'score': r['_score']
    })
  return ret


def get_all_submission_identifiers(rs=None):
  """
  Liefert Liste mit allen Submission-Identifiern zurück
  """
  search = mongo.db.submissions.find({"rs" : rs}, {'identifier': 1, 'urls': 1})
  if search.count():
    slist = []
    for submission in search:
      if 'urls' in submission and len(submission['urls']):
        slist.append({'identifier': submission['identifier'], 'url': submission['urls'][0]})
      else:
        slist.append({'identifier': submission['identifier'], 'url': submission['identifier']})
    return slist


def valid_submission_identifier(identifier):
  """
  Testet, ob der Submission Identifier existiert.
  """
  s = mongo.db.submissions.find_one({'identifier': identifier}, {'_id': 1})
  pprint.pprint(s)
  if s is not None:
    return True
  return False


def get_locations_by_name(rs, streetname):
  """
  Liefert Location-Einträge für einen Namen zurück.
  """
  cursor = mongo.db.locations.find({'name': streetname, "rs" : app.config['RS']})
  streets = []
  for street in cursor:
    streets.append(street)
  return streets


def get_locations(rs, lon, lat, radius=1000):
  """
  Liefert Location-Einträge im Umkreis eines Punkts zurück
  """
  if type(lon) != float:
    lon = float(lon)
  if type(lat) != float:
    lat = float(lat)
  if type(radius) != int:
    radius = int(radius)
  earth_radius = 6371000.0
  res = mongo.db.locations.aggregate([
  {
    '$geoNear': {
    'near': [lon, lat],
    'distanceField': 'distance',
    'distanceMultiplier': earth_radius,
    'maxDistance': (float(radius) / earth_radius),
    'spherical': True
    }
  }])
  streets = []
  for street in res['result']:
    street['distance'] = int(round(street['distance']))
    streets.append(street)
  return streets

def get_responses():
  cursor = mongo.db.responses.find()
  responses = []
  for response in cursor:
    responses.append(response)
  return responses

def add_response(response):
  mongo.db.responses.insert(response)
  return True

