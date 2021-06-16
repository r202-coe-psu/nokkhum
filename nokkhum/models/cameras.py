import mongoengine as me
from flask import current_app
import datetime


class CameraBrand(me.Document):
    meta = {"collection": "camera_brands"}

    name = me.StringField(default="", required=True, max_length=100)
    # camera_models = me.ListField(me.EmbeddedDocumentField(CameraModel))
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now())
    updated_date = me.DateTimeField(
        required=True,
        auto_now=True,
        auto_now_add=False,
        default=datetime.datetime.now(),
    )


class CameraModel(me.Document):
    meta = {"collection": "camera_models"}

    brand = me.ReferenceField("CameraBrand", dbref=True)

    model = me.StringField(required=True, default="", max_length=100)
    port = me.StringField(required=True, default="", max_length=10)
    protocal = me.StringField(
        required=True,
        default="rtsp",
        choices=(("rtsp://", "rtsp://"), ("http://", "http://")),
    )
    path = me.StringField(required=True, default="", max_length=200)

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now())
    updated_date = me.DateTimeField(
        required=True,
        auto_now=True,
        auto_now_add=False,
        default=datetime.datetime.now(),
    )


class MotionProperty(me.EmbeddedDocument):
    active = me.BooleanField(default=False, required=True)
    sensitivity = me.FloatField(min_value=0, max_value=100, default=50, required=True)


class Camera(me.Document):
    meta = {"collection": "cameras"}
    project = me.ReferenceField("Project", dbref=True)
    name = me.StringField(required=True, default="")
    frame_rate = me.FloatField(required=True)
    width = me.IntField(required=True)
    height = me.IntField(required=True)
    location = me.GeoPointField()
    uri = me.StringField(required=True, default="")

    # model = me.ReferenceField("CameraModel", dbref=True)

    status = me.StringField(required=True, default="active")
    motion_property = me.EmbeddedDocumentField(MotionProperty, default=MotionProperty())

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
