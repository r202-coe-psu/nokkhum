import mongoengine as me


class GridView(me.Document):
    meta = {"collection": "gridviews"}
    name = me.StringField(required=True, default="")
    user = me.ReferenceField("User", dbref=True)
    type = me.StringField(required=True, default="grid-4")
    data = me.DictField(required=True, default={})