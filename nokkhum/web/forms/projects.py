from wtforms import fields

from flask_wtf import FlaskForm


class ProjectForm(FlaskForm):
    name = fields.StringField("Project Name")
    has_token = fields.BooleanField("Line Notify", default=False)
    line_notify_token = fields.StringField("Line Notify Token", default="")
