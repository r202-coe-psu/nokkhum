import mongoengine as me
from flask import current_app


class Camera(me.Document):
    meta = {'collection': 'cameras'}

    name = me.StringField(required=True)
    frame_rate = me.FloatField(required=True)
    width = me.IntField(required=True)
    height = me.IntField(required=True)
    location = me.GeoPointField()
    uri = me.StringField(required=True)
    status = me.StringField(required=True, default='active')

    def get_streaming_url(self):
        config = current_app.config
        return '{}/cameras/{}/live'.format(config.get('NOKKHUM_STREAMING_URL'),
                                           str(self.id))

    def get_processor(self):
        from . import processors
        return processors.Processor.objects.get(camera=self)

    def get_project(self):
        from . import projects
        return projects.Project.objects(cameras__contains=self).first()
