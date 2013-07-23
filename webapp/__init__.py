from flask import Flask
from flask.ext.pymongo import PyMongo

from flask.ext.mongo_sessions import MongoDBSessionInterface

app = Flask(__name__)
app.debug = True
app.config.from_pyfile('../config.py')
app.config.from_envvar('CITY_CONF')
mongo = PyMongo(app)

with app.app_context():
    app.session_interface = MongoDBSessionInterface(app, mongo.db, 'flasksessions')

import webapp.views
import webapp.api
