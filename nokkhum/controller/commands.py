from nokkhum import models
import datetime
import asyncio
import logging
logger = logging.getLogger(__name__)


class CommandController:
    def __init__(self, settings):
        self.settings = settings

    def expired_processor_commands(self):
        days = self.settings['DUE_DATE']
        lifetime_date = datetime.datetime.now() - datetime.timedelta(days=days)
        processor_commands = models.ProcessorCommand.objects(
                commanded_date__lt=lifetime_date,
                type='system'
                )
        processor_commands.delete()

    async def handle_controller_after_restart(self, command_q):
        # await asyncio.sleep(20)
        accepted_date = datetime.datetime.now() - datetime.timedelta(seconds=120)
        processors = models.Processor.objects(
                updated_date__lt=accepted_date)
        # ,
        #         state__in=['running', 'start', 'starting'])

        # logger.debug(f'Check and restart processor {processors}')
        for processor in processors:
            # logger.debug(f'check state {processor.state}')
            if processor.user_command.action in ['stop', 'stop-recorder', 'stop-motion-recorder']:
                # logger.debug('command stop')
                if processor.state != 'stop':
                    processor.state = 'stop'
                    processor.save()
                continue

            # data = {'action': processor.user_command.action,
            #         'camera_id': str(processor.camera.id),
            #         'processor_id': str(processor.id),
            #         'project_id': str(processor.project.id),
            #         'system': True}
            
            # await command_q.put(data)
