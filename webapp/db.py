# encoding: utf-8

from webapp import mongo, app
import pyes
import util

from bson import ObjectId
import gridfs

import pprint
import urllib2
import datetime
import dateutil.relativedelta

es = pyes.ES(app.config['ES_HOST']+':'+str(app.config['ES_PORT']))
es.default_indices = [app.config['ES_INDEX_NAME_PREFIX']+'-latest']
es.refresh()


def map_legacy_url(download_path):
    """
    Von legacy-attachment-URL zu neuer Attachment URL.
    download_path ist der Pfad der alten URL, z.B:
    "4/0/pdf227504.pdf"
    """
    (filename, ext) = download_path.split('/')[-1].split('.')
    numeric_id = filename[3:]
    query = {'legacy_id': numeric_id}
    projection = {'_id': 1}
    attachment = mongo.db.attachments.find_one(query, projection)
    if attachment is None:
        return None
    return '/anhang/%s/' % attachment['_id']


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


def get_file(file_id):
    """Return the actual file info"""
    fs = gridfs.GridFS(mongo.db)
    return fs.get(file_id)


def get_submissions(references=None, submission_ids=None, get_attachments=False,
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
            query = {'identifier': r, "rs" : app.config['RS']}
        else:
            if type(r) != ObjectId:
                r = ObjectId(r)
            query = {'_id': r, "rs" : app.config['RS']}
        result = mongo.db.submissions.find(query)
        print result
        for res in result:
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
            if get_consultations:
                # Verweisende agendaitems finden
                sessions = mongo.db.sessions.find({'agendaitems.submissions.$id': res['_id'], "rs" : app.config['RS']})
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


def query_submissions(q='', fq=None, sort='score desc', start=0, docs=10, date=None, facets=None):
    (sort_field, sort_order) = sort.split(' ')
    if sort_field == 'score':
        sort_field = '_score'
    sort = {sort_field: {'order': sort_order}}
    query = pyes.query.BoolQuery()
    query.add_must(pyes.StringQuery(q, default_operator="AND"))
    rest = True
    x = 0
    counter = 0
    result = []
    while rest:
        counter += 1
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
            x = y + 5
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
    print result
    for sfq in result:
        print sfq
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


def get_all_submission_identifiers():
    """
    Liefert Liste mit allen Submission-Identifiern zurück
    """
    search = mongo.db.submissions.find({"rs" : app.config['RS']}, {'identifier': 1})
    if search.count():
        slist = []
        for submission in search:
            slist.append(submission['identifier'])
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


def get_locations_by_name(streetname):
    """
    Liefert Location-Einträge für einen Namen zurück.
    """
    cursor = mongo.db.locations.find({'name': streetname, "rs" : app.config['RS']})
    streets = []
    for street in cursor:
        streets.append(street)
    return streets


def get_locations(lon, lat, radius=1000):
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
