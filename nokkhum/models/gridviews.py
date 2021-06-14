import mongoengine as me


class GridView(me.Document):
    meta = {"collection": "gridviews"}
    name = me.StringField(required=True, default="")
    user = me.ReferenceField("User", dbref=True)
    num_grid = me.IntField(required=True, default=4)
    data = me.DictField(required=True, default={})