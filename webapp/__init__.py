from flask import Flask
from flask.ext.pymongo import PyMongo
from flask.ext.bootstrap import Bootstrap
from flask.ext.basicauth import BasicAuth
from flask.ext.cache import Cache
from flask.ext.mongo_sessions import MongoDBSessionInterface


app = Flask(__name__)
app.debug = True
app.config.from_pyfile('../config.py')

# Cache
cache = Cache(app, config={'CACHE_TYPE': 'memcached', 'CACHE_MEMCACHED_SERVERS': ['127.0.0.1:11211']})
cache.init_app(app)

# Bootstrap
bootstrap = Bootstrap(app)

# SimpleAuth
basic_auth = BasicAuth(app)

mongo = PyMongo(app)

# Sessions and Configuration
import db
with app.app_context():
  app.session_interface = MongoDBSessionInterface(app, mongo.db, 'flasksessions')
  app.config.update(db.get_config())
  
import webapp.views
import webapp.api
import webapp.oparl