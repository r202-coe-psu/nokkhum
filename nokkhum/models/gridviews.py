import mongoengine as me


class GridView(me.Document):
    meta = {"collection": "gridviews"}
    name = me.StringField(required=True)
    project = me.ReferenceField("Project", dbref=True)
    user = me.ReferenceField("User", dbref=True)
    type = me.StringField(required=True, default="grid-4")
    cameras = me.ListField(me.ReferenceField("Camera", dbref=True))
