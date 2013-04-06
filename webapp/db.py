# encoding: utf-8

from webapp import mongo
import util

from bson import ObjectId
import gridfs

import pprint


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


def get_submissions(references, get_attachments=False,
                    get_consultations=False, get_thumbnails=False):
    """
    Liefert die in der Liste references identifizierten
    Drucksachen zurück
    """
    submissions = {}
    for r in references:
        result = mongo.db.submissions.find({'identifier': r})
        for res in result:
            if get_attachments:
                # Zugehörige attachments einfügen
                if 'attachments' in res:
                    for n in range(len(res['attachments'])):
                        a = res['attachments'][n]
                        res['attachments'][n] = mongo.db.attachments.find_one({'_id': a.id})
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
                        agendaitems = session['agendaitems']
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
            submissions[str(res['_id'])] = res
    return submissions.values()


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
    print "Identifier", identifier
    s = mongo.db.submissions.find_one({'identifier': identifier}, {'_id': 1})
    pprint.pprint(s)
    if s is not None:
        return True
    return False
