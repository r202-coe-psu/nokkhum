import mongoengine as me
import datetime


class GridView(me.Document):
    meta = {"collection": "gridviews"}
    name = me.StringField(required=True, default="")
    user = me.ReferenceField("User", dbref=True)
    num_grid = me.IntField(required=True, default=4)
    data = me.DictField(required=True, default={})

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now())
    updated_date = me.DateTimeField(
        required=True,
        auto_now=True,
        auto_now_add=False,
        default=datetime.datetime.now(),
    )
