import pickle
import uuid
from datetime import datetime
from datetime import timedelta

from bson.binary import Binary

from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionMixin
from flask.sessions import SessionInterface


class MongoDBSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=True):
        def on_update(this):
            this.modified = True
        if initial:
            initial = pickle.loads(str(initial))
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False

    def pack(self):
        return Binary(pickle.dumps(dict(self)))


class MongoDBSessionInterface(SessionInterface):
    session_class = MongoDBSession

    def __init__(self, app, db, collection_name):
        self._db = db
        self._collection_name = collection_name

        if app is not None:
            self.app = app
            self.init_app(app)
        else:
            self.app = None

    def init_app(self, app):
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['mongodb-sessions'] = self

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.__generate_sid()
            return self.session_class(sid=sid)

        doc = self.__get_collection().find_one({'_id': sid})
        # Check if exists and not expired.
        # It's ok to remove tzinfo here, because utcnow() returns UTC time,
        # despite it's in naive form (without tzinfo).
        if doc and doc['exp'].replace(tzinfo=None) > datetime.utcnow():
            session = self.session_class(initial=doc['d'], sid=sid)
        else:
            # If the SID doesn't exist - create a new one to avoid possibility
            # of user-generated SID with invalid format (e.g. "abc123").
            sid = self.__generate_sid()
            session = self.session_class(sid=sid)
        return session

    def save_session(self, app, session, response):
        # cookie_domain = self.get_cookie_domain(app)
        # cookie_path = self.get_cookie_path(app)
        cookie_exp = self.get_expiration_time(app, session)

        if not session:
            self.__get_collection().remove({'_id': session.sid})
            if session.modified:
                response.delete_cookie(key=app.session_cookie_name,
                                       #path=cookie_path,
                                       #domain=cookie_domain
                                       )
            return

        # If session isn't permanent if will be considered valid for 1 day
        # (but not cookie which will be deleted by browser after exit).
        session_exp = cookie_exp or datetime.utcnow()+timedelta(days=1)
        self.__get_collection().update(
            {'_id': session.sid},
            {'$set': {
                'd': session.pack(),
                'exp': session_exp,
            }},
            upsert=True)

        response.set_cookie(key=app.session_cookie_name,
                            value=session.sid,
                            expires=cookie_exp,
                            #path=cookie_path,
                            #domain=cookie_domain,
                            secure=self.get_cookie_secure(app),
                            httponly=self.get_cookie_httponly(app))

    def __get_collection(self):
        return self._db[self._collection_name]

    def __generate_sid(self):
        return uuid.uuid4().hex
