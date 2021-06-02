import mongoengine as me
import datetime


class Project(me.Document):
    meta = {"collection": "projects"}
    name = me.StringField(default="")
    has_token = me.BooleanField(default=False)
    line_notify_token = me.StringField(default="")
    owner = me.ReferenceField("User", dbref=True, required=True)
    assistant = me.ListField(me.ReferenceField("User", dbref=True))
    users = me.ListField(me.ReferenceField("User", dbref=True))
    # cameras = me.ListField(me.ReferenceField("Camera", dbref=True))
    status = me.StringField(required=True, default="active")
    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now, auto_now=True
    )

    @property
    def cameras(self):
        from . import Camera

        return Camera.objects(project=self, status="active")

    def camera_is_active(self):
        count = 0
        for camera in self.cameras:
            if camera.status == "active":
                count += 1
        return count

    def is_member(self, user):
        if user in self.users or user in self.assistant or self.owner.id == user.id:
            return True
        return False

    def is_assistant_or_owner(self, user):
        if user in self.assistant or self.owner.id == user.id:
            return True
        return False

    def is_owner(self, user):
        if self.owner.id == user.id:
            return True
        return False