from wtforms import fields
from wtforms import validators
from flask_wtf import FlaskForm
from flask_mongoengine.wtf import model_form

from nokkhum import models


class CameraForm(FlaskForm):
    name = fields.StringField("Camera Name")
    frame_rate = fields.FloatField(default=15)
    frame_size = fields.SelectField("Frame Size")
    # width = fields.FloatField()
    # height = fields.FloatField()
    latitude = fields.FloatField(
        "Latitude", validators=[validators.NumberRange(min=-180, max=180)]
    )
    longitude = fields.FloatField(
        "Longitude", validators=[validators.NumberRange(min=-180, max=180)]
    )
    uri = fields.StringField("URI")

    storage_period = fields.IntegerField(
        "Storage Period (Days)", default=30, validators=[validators.NumberRange(min=0)]
    )
    motion_detector = fields.BooleanField("Motion Detector", default=False)
    sensitivity = fields.FloatField(
        "Sensitivity", default=50, validators=[validators.NumberRange(min=0, max=100)]
    )

    # username = fields.StringField('Username')
    # password = fields.PasswordField('Password')
    # ip_address = fields.StringField('IP Address', validators=[validators.InputRequired()])
    # port = fields.StringField('Port', validators=[validators.InputRequired()])


BaseCameraBrandForm = model_form(
    models.CameraBrand,
    FlaskForm,
    only=["name"],
    field_args={
        "name": {"label": "Camera Brand Name"},
    },
)


class CameraBrandForm(BaseCameraBrandForm):
    pass


BaseCameraModelForm = model_form(
    models.CameraModel,
    FlaskForm,
    only=["model", "protocal", "path", "port"],
    field_args={
        "model": {"label": "Camera Model Name"},
        "protocal": {"label": "Protocal"},
        "path": {"label": "Path"},
        "port": {"label": "Port"},
    },
)


class CameraModelForm(BaseCameraModelForm):
    pass
