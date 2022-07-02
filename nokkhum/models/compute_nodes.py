import mongoengine as me
import datetime

MAX_RECORD = 10


class MachineSpecification(me.EmbeddedDocument):
    cpu_model = me.StringField()
    cpu_frequency = me.FloatField()
    cpu_count = me.IntField()
    machine = me.StringField()
    system = me.StringField()
    name = me.StringField()
    total_memory = me.IntField()
    total_disk = me.IntField()


class CPUUsage(me.EmbeddedDocument):
    used = me.FloatField(default=0)  # show in percent
    used_per_cpu = me.ListField(me.FloatField())


class MemoryUsage(me.EmbeddedDocument):
    used = me.IntField(default=0)
    free = me.IntField(default=0)
    total = me.IntField(required=True, default=0)


class DiskUsage(me.EmbeddedDocument):
    used = me.IntField(default=0)
    free = me.IntField(default=0)
    percent = me.FloatField(default=0)  # show in percent
    total = me.IntField(required=True, default=0)


class SystemLoad(me.EmbeddedDocument):
    cpu = me.FloatField(default=0)
    memory = me.IntField(default=0)


class ResourceUsage(me.EmbeddedDocument):
    cpu = me.EmbeddedDocumentField("CPUUsage", required=True, default=CPUUsage())
    memory = me.EmbeddedDocumentField(
        "MemoryUsage", required=True, default=MemoryUsage()
    )
    disk = me.EmbeddedDocumentField("DiskUsage", required=True, default=DiskUsage())
    system_load = me.EmbeddedDocumentField(
        "SystemLoad", required=True, default=SystemLoad()
    )

    reported_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    # report = me.ReferenceField('ComputeNodeReport')


class ComputeNode(me.Document):
    meta = {"collection": "compute_nodes"}

    name = me.StringField(max_length=100, required=True)
    ip = me.StringField(max_length=100, required=True, index=True)
    mac = me.StringField(max_length=100, required=True, index=True)

    machine_specification = me.EmbeddedDocumentField(MachineSpecification)

    resource_records = me.ListField(me.EmbeddedDocumentField(ResourceUsage))

    created_date = me.DateTimeField(required=True, default=datetime.datetime.now)
    updated_date = me.DateTimeField(required=True, default=datetime.datetime.now)

    updated_resource_date = me.DateTimeField(
        required=True, default=datetime.datetime.now
    )

    extra = me.DictField()

    def is_online(self):
        delta = datetime.timedelta(minutes=1)
        now = datetime.datetime.now()

        if self.updated_resource_date > now - delta:
            resource = self.get_current_resources()
            if resource is None:
                return False

            if resource.cpu.used > 0 or resource.memory.used > 0:
                return True

        return False

    def get_current_resources(self):
        if len(self.resource_records) == 0:
            return None

        return self.resource_records[-1]

    def push_resource(self, resource_usage):
        while len(self.resource_records) > MAX_RECORD:
            self.resource_records.pop(0)

        self.resource_records.append(resource_usage)

    def push_responsed_date(self, added_date=None):
        if "responsed_date" not in self.extra:
            self.extra["responsed_date"] = list()

        while len(self.extra["responsed_date"]) > MAX_RECORD:
            self.extra["responsed_date"].pop(0)

        if added_date is None:
            added_date = datetime.datetime.now()

        self.extra["responsed_date"].append(added_date)
