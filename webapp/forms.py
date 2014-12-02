# encoding: utf-8

from flask.ext.wtf import Form
from wtforms import validators
from wtforms import SubmitField, TextField, SelectField, FileField, TextAreaField, HiddenField, BooleanField
from webapp import app, db

class ConfigForm(Form):
  config = TextAreaField(
    label=u'Konfiguration als JSON',
    validators=[validators.Required(), validators.Length(max=32000)],
    description='')
  submit = SubmitField(
    label=u'Daten speichern')
  
class BodyForm(Form):
  config = TextAreaField(
    label=u'Konfiguration als JSON',
    validators=[validators.Required(), validators.Length(max=32000)],
    description='')
  submit = SubmitField(
    label=u'Daten speichern')