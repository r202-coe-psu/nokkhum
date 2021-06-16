from nokkhum import models

from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm
from wtforms import fields

BaseProjectForm = model_form(
    models.StorageShare,
    FlaskForm,
    only=["psu_passport_username"],
    field_args={
        "psu_passport_username": {"label": "PSU Passport Username"},
    },
)


class ShareStorageForm(BaseProjectForm):
    # psu_passport_username = fields.SelectField("PSU Passport Username")
    start_date = fields.StringField("Start Date")
    expire_date = fields.StringField("Expire Date")
