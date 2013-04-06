# encoding: utf-8

import time
import datetime
import email.utils
import calendar
import json
import bson
import pprint

from webapp import app

def rfc1123date(value):
    """
    Gibt ein Datum (datetime) im HTTP Head-tauglichen Format (RFC 1123) zurück
    """
    tpl = value.timetuple()
    stamp = calendar.timegm(tpl)
    return email.utils.formatdate(timeval=stamp, localtime=False, usegmt=True)


def parse_rfc1123date(string):
    return datetime.datetime(*email.utils.parsedate(string)[:6])


def expires_date(hours):
    """Date commonly used for Expires response header"""
    dt = datetime.datetime.now() + datetime.timedelta(hours=hours)
    return rfc1123date(dt)


def cache_max_age(hours):
    """String commonly used for Cache-Control response headers"""
    seconds = hours * 60 * 60
    return 'max-age=' + str(seconds)


def attachment_url(attachment_id, filename=None, extension=None):
    if filename is not None:
        extension = filename.split('.')[-1]
    return app.config['ATTACHMENT_DOWNLOAD_URL'] % (attachment_id, extension)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, bson.ObjectId):
            return str(obj)
        elif isinstance(obj, bson.DBRef):
            return {
                'collection': obj.collection,
                '_id': obj.id
            }
        return obj.__dict__
