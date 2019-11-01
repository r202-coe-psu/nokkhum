from nokkhum import models
import asyncio 
import logging
logger = logging.getLogger(__name__)


class ProcessorController:
    def __init__(self):
        pass

    def get_processor(self, project, camera):
        processor = models.Processor.objects(
                project=project,
                camera=camera).first()

        if processor:
            return processor

        processor = models.Processor(
                project=project,
                camera=camera)
        processor.save()

        return processor

    def process_command(self, data):
        # logger.debug('in process command ')
        camera = models.Camera.objects(id=data['camera_id']).first()
        project = models.Project.objects(id=data['project_id']).first()
        if not 'systemctrl' in data:
            user = models.User.objects(id=data['user_id']).first()
            processor = self.get_processor(project, camera)
            processor_command = models.ProcessorCommand(
                    processor=processor,
                    action=data['action'],
                    owner=user,
                    type='user')
            processor.user_command = processor_command
             
            # logger.debug('not system') 
        
        elif 'systemctrl' in data:
            processor = models.Processor.objects.get(id=data['processor_id'])
            processor_command = models.ProcessorCommand(
                    processor=processor,
                    action=data['action'],
                    type='system')
            
            # logger.debug('by system') 
        
        # logger.debug('before save')
        processor.reference_command = processor_command
        processor_command.save()
        processor.state = data['action']
        processor.save()
        # logger.debug('after save')

        return processor

    async def update_fail_processor(self, data, compute_node_id, command_q):
        # processor = self.get_processor(project, camera)
        # processor_id = next(iter(data['dead_process']))
        # logger.debug(next(iter(data['dead_process'])))
        # logger.debug('in update fail')
        compute_node = models.ComputeNode.objects.get(id=compute_node_id)
        for processor_id, msg in data['dead_process'].items():
            processor = models.Processor.objects.get(id=processor_id)
            processor.state = 'stop'
            processor.save()
            fail_processor = models.FailRunningProcessor(
                    processor=processor,
                    compute_node=compute_node,
                    message=msg
                    )
            fail_processor.save()
            if processor.user_command.action == 'start':
                logger.debug('Try to restart')
                data = {'action': 'start',
                        'camera_id': str(processor.camera.id),
                        'processor_id': str(processor.id),
                        'project_id': str(processor.project.id),
                        'systemctrl': True}
                await command_q.put(data)
