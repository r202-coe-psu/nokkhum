from wtforms import fields
from wtforms import Form


class SearchForm(Form):
    number = fields.StringField('')
    province = fields.StringField('')
    detected_date = fields.DateTimeField('')

