from nokkhum import models
import datetime
import asyncio
import logging
logger = logging.getLogger(__name__)


class CommandController:
    def __init__(self, settings):
        self.settings = settings

    async def remove_expired_processor_commands(self):
        days = self.settings['DUE_DATE']
        lifetime_date = datetime.datetime.now() - datetime.timedelta(days=days)
        processor_commands = models.ProcessorCommand.objects(
                commanded_date__lt=lifetime_date,
                type='system'
                )
        processor_commands.delete()

    async def restart_processors(self, command_q):
        # await asyncio.sleep(20)
        logger.debug('check and restart processor' )
        accepted_date = datetime.datetime.now() - datetime.timedelta(seconds=120)
        pipeline = [
                {
                    '$lookup': {
                        'from': 'processor_commands',
                        'localField': 'user_command.recorder.$id',
                        'foreignField': '_id',
                        'as': 'recorder',
                    }
                },
                {
                    '$addFields': {
                        "recorder": { '$arrayElemAt': ["$recorder", 0] }
                    }
                },
                {
                    '$match': {
                        'recorder.action': 'start-recorder'
                    }
                }
                ]

        processors = models.Processor.objects(
                updated_date__lt=accepted_date
                ) \
                .aggregate(pipeline)

        for processor in processors:
            logger.debug(f'check state {processor["state"]}')

            data = {'action': processor["recorder"]["action"],
                    'camera_id': str(processor["camera"].id),
                    'processor_id': str(processor["_id"]),
                    'project_id': str(processor["project"].id),
                    'system': True}

            await command_q.put(data)
