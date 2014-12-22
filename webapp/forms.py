# encoding: utf-8

from flask.ext.wtf import Form
from wtforms import validators
from wtforms import SubmitField, TextField, SelectField, FileField, TextAreaField, HiddenField, BooleanField, DecimalField, FloatField, IntegerField
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
  
class RegionForm(Form):
  name = TextField(
    label=u'Name',
    validators=[validators.Required(), validators.Length(max=32000)],
    description='')
  type = IntegerField(
    label=u'Typus (im OSM Sinne). Stadt = 1, Region = 2',
    validators=[validators.Required(), validators.NumberRange(min=1, max=2)],
    description='',
    default=0)
  bodies = TextAreaField(
    label=u'Bodies, pro Zeile eine ID',
    validators=[validators.Required(), validators.Length(max=32000)],
    description='')
  keywords = TextAreaField(
    label=u'Keywords, pro Zeile ein String',
    validators=[validators.Required(), validators.Length(max=32000)],
    description='')
  lat = FloatField(
    label=u'Lat',
    validators=[validators.Required(), validators.NumberRange(min=47.2, max=55.0)],
    description='',
    default=0.0)
  lon = FloatField(
    label=u'Lon',
    validators=[validators.Required(), validators.NumberRange(min=5.5, max=15.1)],
    description='',
    default=0.0)
  zoom = IntegerField(
    label=u'Zoom',
    validators=[validators.Required(), validators.NumberRange(min=1, max=18)],
    description='',
    default=0)
  submit = SubmitField(
    label=u'Daten speichern')