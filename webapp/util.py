# encoding: utf-8

import datetime
import email.utils
import calendar
import json
import bson
import re
import urllib
import urllib2
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


def thumbnail_url(attachment_id, size, page):
    attachment_id = str(attachment_id)
    url = app.config['THUMBS_URL']
    url += attachment_id[-1] + '/' + attachment_id[-2] + '/' + attachment_id
    url += '/' + str(size)
    url += '/' + str(page) + '.' + app.config['THUMBNAILS_SUFFIX']
    return url


def submission_url(identifier):
    url = app.config['BASE_URL']
    url += 'dokumente/' + urllib.quote_plus(identifier) + '/'
    return url


def geocode(location_string):
    """
    Löst eine Straßen- und optional PLZ-Angabe zu einer Geo-Postion
    auf. Beispiel: "Straßenname (12345)"
    """
    postal = None
    street = location_string.encode('utf-8')
    postalre = re.compile(r'(.+)\s+\(([0-9]{5})\)')
    postal_matching = re.match(postalre, street)
    postal = None
    if postal_matching is not None:
        street = postal_matching.group(1)
        postal = postal_matching.group(2)
    url = 'http://open.mapquestapi.com/nominatim/v1/search.php'
    params = {'format': 'json',  # json
              'q': ' '.join([street, app.config['GEOCODING_DEFAULT_CITY']]),
              'addressdetails': 1,
              'accept-language': 'de_DE',
              'countrycodes': app.config['GEOCODING_DEFAULT_COUNTRY']}
    request = urllib2.urlopen(url + '?' + urllib.urlencode(params))
    response = request.read()
    addresses = json.loads(response)
    addresses_out = []
    for n in range(len(addresses)):
        for key in addresses[n].keys():
            if key in ['address', 'boundingbox', 'lat', 'lon', 'osm_id']:
                continue
            del addresses[n][key]
        # skip if no road contained
        if 'road' not in addresses[n]['address']:
            continue
        # skip if not in correct county
        if 'county' not in addresses[n]['address']:
            continue
        if addresses[n]['address']['county'] != app.config['GEOCODING_FILTER_COUNTY']:
            continue
        if postal is not None:
            if 'postcode' in addresses[n]['address'] and addresses[n]['address']['postcode'] == postal:
                addresses_out.append(addresses[n])
        else:
            print "yay"
            addresses_out.append(addresses[n])
    return addresses_out


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
