'''
Created on Nov 8, 2011

@author: boatkrap
'''

import mongoengine as me
import datetime

PROCESSOR_OPERATING_STATE = [
        'start', 'starting', 'running', 'stopping', 'stop']
PROCESSOR_USER_COMMANDS = [
        'start',
        'start-recorder',
        'start-motion-recorder',
        'start-streamer',
        'stop',
        'stop-recorder',
        'stop-motion-recorder',
        'stop-streamer',
        'suspend',
        ]

MAX_RECORE = 20


class ProcessorReport(me.EmbeddedDocument):
    cpu = me.FloatField(required=True, default=0)
    memory = me.IntField(required=True, default=0)
    num_threads = me.IntField(required=True, default=0)
    reported_data = me.DateTimeField(
            required=True,
            default=datetime.datetime.now)
    created_date = me.DateTimeField(
            required=True,
            default=datetime.datetime.now)
    compute_node = me.ReferenceField('ComputeNode', dbref=True)

    processors = me.DictField()


class UserProcessorCommand(me.EmbeddedDocument):
    streamer = me.ReferenceField('ProcessorCommand', dbref=True)
    recorder = me.ReferenceField('ProcessorCommand', dbref=True)


class Processor(me.Document):
    meta = {
            'collection': 'processors',
            # 'strict': False,
            }

    camera = me.ReferenceField('Camera', dbref=True)
    storage_period = me.IntField(required=True, default=30)  # in day

    # image_processors = me.ListField(me.DictField())
    status = me.StringField(required=True, default='active')

    created_date = me.DateTimeField(
            required=True,
            default=datetime.datetime.now)
    updated_date = me.DateTimeField(
            required=True,
            auto_now=True,
            auto_now_add=False,
            default=datetime.datetime.now)

    project = me.ReferenceField('Project', required=True, dbref=True)
    # owner = me.ReferenceField('User', required=True, dbref=True)

    user_command = me.EmbeddedDocumentField(
            UserProcessorCommand,
            default=UserProcessorCommand())
    # last_command = me.ReferenceField('ProcessorCommand', dbref=True)
    # reference_command = me.ReferenceField('ProcessorCommand', dbref=True)

    state = me.StringField(required=True,
                           default='stop',
                           choices=PROCESSOR_OPERATING_STATE)

    compute_node = me.ReferenceField('ComputeNode', dbref=True)
    reports = me.ListField(me.EmbeddedDocumentField('ProcessorReport'))


    def push_processor_report(self, report):
        if len(self.reports) > MAX_RECORE:
            self.reports.pop(0)

        self.reports.append(report)

    def update_user_command(self, processor_command):
        if processor_command.type != 'user':
            return

        if 'streamer' in processor_command.action:
            self.user_command.streamer = processor_command
        elif 'recorder' in processor_command.action:
            self.user_command.recorder = processor_command

    def count_system_start_recorder(self, seconds=10):
        after_time = datetime.datetime.now() - datetime.timedelta(seconds=seconds)
        
        count = ProcessorCommand.objects(
                processor=self,
                action__in=['start-recorder', 'start-motion_recorder'],
                type='system',
                commanded_date__gt=after_time,
                ).count()

        return count

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        document.updated_date = datetime.datetime.now()
    # def camera_is_running(self):
    #     # if camera == self.camera:
    #     if self.state == 'stop' or self.state == 'stopping':
    #         return False
    #     else:
    #         return True


me.signals.pre_save.connect(Processor.pre_save, sender=Processor)


class ProcessorCommand(me.Document):
    meta = {'collection': 'processor_commands'}

    processor = me.ReferenceField('Processor', dbref=True)
    # attributes = me.DictField()
    action = me.StringField(required=True,
                            default='suspend',
                            choices=PROCESSOR_USER_COMMANDS)
    # status = me.StringField(required=True, default='waiting')
    # compute_node = me.ReferenceField('ComputeNode', dbref=True)

    type = me.StringField(required=True, default='system')
    commanded_date = me.DateTimeField(
        required=True, default=datetime.datetime.now)
    processed_date = me.DateTimeField(
        required=True, default=datetime.datetime.now)

    completed_date = me.DateTimeField()
    completed = me.BooleanField(required=True, default=False)
    # updated_date = me.DateTimeField(
    #     required=True, default=datetime.datetime.now)
    owner = me.ReferenceField('User', dbref=True)
    message = me.StringField(required=True, default='')

    # extra = me.DictField()

    # command_type_option = ['system', 'user']


class FailRunningProcessor(me.Document):
    meta = {'collection': 'fail_running_processors'}

    processor = me.ReferenceField('Processor', dbref=True)
    compute_node = me.ReferenceField('ComputeNode', dbref=True)
    reported_date = me.DateTimeField(
        required=True, default=datetime.datetime.now)
    processed_date = me.DateTimeField(
        required=True, default=datetime.datetime.now)
    message = me.StringField(required=True, default='')
