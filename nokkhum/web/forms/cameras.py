from wtforms import fields
from wtforms import validators
from flask_wtf import FlaskForm


class CameraForm(FlaskForm):
    name = fields.StringField('Camera Name')
    frame_rate = fields.FloatField()
    width = fields.FloatField()
    height = fields.FloatField()
    latitude = fields.FloatField('Latitude', default=0,
                                 validators=[validators.NumberRange(min=-180, max=180)])
    longitude = fields.FloatField('Longitude', default=0,
                                  validators=[validators.NumberRange(min=-180, max=180)])
    uri = fields.StringField('URI')
    storage_period = fields.IntegerField('Storage Period (day)', default=30,
                                         validators=[validators.NumberRange(min=0)])
