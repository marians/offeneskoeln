from flask import Flask
from flask.ext.pymongo import PyMongo

app = Flask(__name__)
app.config.from_pyfile('../config.py')
mongo = PyMongo(app)

import webapp.views
import webapp.api
