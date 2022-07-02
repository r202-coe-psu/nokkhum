import mongoengine as me
import datetime


class StorageShare(me.Document):
    meta = {"collection": "storage_share"}

    processor = me.ReferenceField("Processor", dbref=True, required=True)
    date_dir = me.StringField(default="", required=True)

    psu_passport_username = me.StringField(default="", required=True, max_length=100)

    start_date = me.DateField(required=True, default=datetime.date.today())
    expire_date = me.DateField(required=True, default=datetime.date.today())

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now())
    updated_date = me.DateTimeField(
        required=True, default=datetime.datetime.now(), auto_now=True
    )

    def check_permission(self):
        if self.start_date <= datetime.date.today() <= self.expire_date:
            return True
        return False
