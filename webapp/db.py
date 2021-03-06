# encoding: utf-8

from webapp import mongo
import pyes
import util

from bson import ObjectId
import gridfs

import pprint

es = pyes.ES('localhost:9200')
es.default_indices = ['offeneskoeln-latest']
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
            query = {'identifier': r}
        else:
            if type(r) != ObjectId:
                r = ObjectId(r)
            query = {'_id': r}
        result = mongo.db.submissions.find(query)
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
                sessions = mongo.db.sessions.find({'agendaitems.submissions.$id': res['_id']})
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
    string_query = pyes.StringQuery(q, default_operator="AND")
    search = pyes.query.Search(query=string_query, fields=[''], start=start, size=docs, sort=sort)
    result = es.search(search, model=lambda x, y: y)
    ret = {
        'numhits': result.total,
        'maxscore': result.max_score,
        'result': []
    }
    if result.max_score is not None:
        ret['maxscore'] = result.max_score
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
    search = mongo.db.submissions.find({}, {'identifier': 1})
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
    cursor = mongo.db.locations.find({'name': streetname})
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
