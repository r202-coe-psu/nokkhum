import datetime
import asyncio
import json

import logging
logger = logging.getLogger(__name__)

from nokkhum import models

class ProcessorController:
    def __init__(self, nc=None):
        self.nc = nc

    async def init_message(self, nc):
        self.nc = nc

    async def get_processor(self, project, camera):
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



    async def get_available_compute_node(self):
        deadline_date = datetime.datetime.now() - datetime.timedelta(seconds=60)

        # need a scheduling
        compute_node = models.ComputeNode.objects(
            updated_date__gt=deadline_date
        ).first()

        return compute_node


    async def process_command(self, data):
        camera = models.Camera.objects(id=data["camera_id"]).first()

        if camera is None:
            logger.debug("camera is None")
            return False

        processor = None

        if data.get('processor_id', None) is not None:
            processor = models.Processor.objects(id=data['processor_id']).first()
        else:
            project = models.Project.objects(id=data['project_id']).first()
            processor = await self.get_processor(project, camera)

        result = await self.actuate_command(processor, camera, data)
        return result

        logger.debug('before find processor')
        logger.debug('end find processor')
       # save data into database



    async def actuate_command(self, processor, camera, data):

        # logger.debug('in actuate command ')
        if data.get('system', False):
            user = models.User.objects(id=data['user_id']).first()
            processor_command = models.ProcessorCommand(
                    processor=processor,
                    # action=data['action'],
                    owner=user,
                    type='user')
            processor.user_command = processor_command
             
        else:
            processor_command = models.ProcessorCommand(
                    processor=processor,
                    # action=data['action'],
                    type='system')
 

        compute_node = None
        if data['action'] == 'start-recorder':
            compute_node = await self.get_available_compute_node()

            if compute_node is None:
                logger.debug("compute node is not available for start")
                return False

            processor.compute_node = compute_node
        else:
            compute_node = processor.compute_node

            if compute_node and not compute_node.is_online():
                logger.debug(f"compute node {compute_node.name} is not online")
                return False

        # need to decision
        processor_command.action = data['action']
        if 'start' in data['action']:
            processor.state = 'start'

        processor.reference_command = processor_command
        processor_command.save()
        processor.save()

        if 'start' in data["action"]:
            processor.state = "starting"
        elif 'stop' in data["action"]:
            processor.state = "stopping"
        processor.save()

        command = dict(processor_id=str(processor.id), action=data["action"])
        if data["action"] == "start-recorder":
            command["attributes"] = dict(
                video_uri=camera.uri,
                fps=camera.frame_rate,
                size=(camera.width, camera.height),
                camera_id=str(camera.id),
            )

        topic = "nokkhum.compute.{}.rpc".format(compute_node.mac)

        try:
            result = await self.nc.request(
                topic, json.dumps(command).encode(), timeout=60
            )
        except Exception as e:
            logger.exception(e)
            if 'start' in data["action"]:
                return False

        logger.debug(f"=> processor result {result.data.decode()}")
        result_data = json.loads(result.data.decode())
        logger.debug(f"processor result {result_data}")

        if result_data["success"]:
            if 'start' in data["action"]:
                processor.state = "running"
            elif 'stop' in data["action"]:
                processor.state = "stop"
        else:
            if 'stop' in data["action"]:
                processor.state = "stop"
        processor.save()
        logger.debug(f"end {result_data}")

        return True



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
                data = {'action': 'start-recorder',
                        'camera_id': str(processor.camera.id),
                        'processor_id': str(processor.id),
                        'project_id': str(processor.project.id),
                        'system': True}
                await command_q.put(data)
