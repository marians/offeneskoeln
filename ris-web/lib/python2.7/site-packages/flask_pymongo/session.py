# Copyright (c) 2011-2012, Dan Crosta
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from uuid import UUID, uuid4

from flask.sessions import SessionMixin
from flask.sessions import SessionInterface

class PyMongoSession(dict, SessionMixin):
    pass

class PyMongoSessionInterface(SessionInterface):
    """Implement :class:`flask.sessions.SessionInterface` with session
    backing storage in MongoDB rather than in a secure cookie.

    Rather than instantiating this class yourself, it is recommended to
    use set `sessions` to `True` on your :class:`~flask_pymongo.PyMongo`
    instance.
    """

    def __init__(self, config_prefix, session_cookie='session', collection='sessions'):
        self.config_prefix = config_prefix
        self.session_cookie = session_cookie
        self.collection = collection

    def open_session(self, app, request):
        """If the request has a cookie set with :attr:`_session_id`, attempt
        to load the session with the given identifier from MongoDB. If it is
        found, return a :class:`flask_pymongo.sessions.Session`; if not, return
        ``None``.
        """
        try:
            session_id = UUID(request.cookies.get(self.session_cookie))
            cx, db = app.extensions['pymongo'][self.config_prefix]
        except (ValueError, KeyError):
            return None

        session = db[self.collection].find_one(session_id)
        if session:
            return PyMongoSession(session)
        return None

    def save_session(self, session, response):
        """Save the session to MongoDB.
        """
        if not isinstance(session, PyMongoSession):
            raise TypeError('session (%r) is not a PyMongoSession' % session)

        try:
            cx, db = app.extensions['pymongo'][self.config_prefix]
        except KeyError:
            raise Exception('could not find PyMongo with config prefix %r in app' %
                            self.config_prefix)

        db[self.collection].save(session)
