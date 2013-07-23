from flask import Flask
from flask.ext.pymongo import PyMongo
from flask import request

from flask.ext.mongo_sessions import MongoDBSessionInterface

app = Flask(__name__)
app.debug = True
app.config.from_pyfile('../config.py')
if request.headers['Host'] in app.config['DOMAINS']:
    app.config.from_pyfile('../city/' + app.config['DOMAINS'][request.headers['Host']])

    mongo = PyMongo(app)
    
    with app.app_context():
        app.session_interface = MongoDBSessionInterface(app, mongo.db, 'flasksessions')
    
    import webapp.views
    import webapp.api
else:
    abort(404)