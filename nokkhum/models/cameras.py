import mongoengine as me
from flask import current_app


class CameraModel(me.EmbeddedDocument):
    name = me.StringField(required=True)
    format_parameter = me.ListField(me.StringField)
    rtsp_url = me.StringField(required=True)

class MotionProperty(me.EmbeddedDocument):
    active = me.BooleanField(default=False, required=True)
    sensitivity = me.FloatField(min_value=0, max_value=100, default=50, required=True)

class Camera(me.Document):
    meta = {"collection": "cameras"}
    project = me.ReferenceField("Project", dbref=True)
    name = me.StringField(required=True)
    frame_rate = me.FloatField(required=True)
    width = me.IntField(required=True)
    height = me.IntField(required=True)
    location = me.GeoPointField()
    uri = me.StringField(required=True)
    status = me.StringField(required=True, default="active")
    motion_property = me.EmbeddedDocumentField(MotionProperty)

    def get_streaming_url(self):
        config = current_app.config
        return "{}/live/cameras/{}".format(
            config.get("NOKKHUM_STREAMING_URL"), str(self.id)
        )

    def get_processor(self):
        from . import processors

        return processors.Processor.objects.get(camera=self)

    def get_project(self):
        from . import projects

        return projects.Project.objects(cameras__contains=self).first()


class CameraBrand(me.Document):
    meta = {"collection": "camera_brands"}

    name = me.StringField(required=True)
    camera_models = me.ListField(me.EmbeddedDocumentField(CameraModel))
