import datetime
import asyncio
import json

import logging

logger = logging.getLogger(__name__)

from nokkhum import models


class ProcessorController:
    def __init__(self, nc=None, command_controller=None):
        self.nc = nc
        self.command_controller = command_controller

    async def init_message(self, nc):
        self.nc = nc

    async def get_processor(self, project, camera):
        processor = models.Processor.objects(project=project, camera=camera).first()

        if processor:
            return processor

        processor = models.Processor(project=project, camera=camera)
        processor.save()

        return processor

    async def get_available_compute_node(self, compute_node=None):
        if compute_node and compute_node.is_online():
            return compute_node

        deadline_date = datetime.datetime.now() - datetime.timedelta(seconds=60)

        # need a scheduling
        compute_node = models.ComputeNode.objects(
            updated_date__gt=deadline_date
        ).first()

        logger.debug(f"compute node {compute_node}")

        return compute_node

    async def process_command(self, data):
        camera = models.Camera.objects(id=data["camera_id"]).first()

        if camera is None:
            logger.debug("camera is None")
            return False

        await asyncio.sleep(0)
        processor = None

        if data.get("processor_id", None) is not None:
            processor = models.Processor.objects(id=data["processor_id"]).first()
        else:
            processor = models.Processor.objects(camera=camera).first()

            if not processor:
                project = models.Project.objects(id=data["project_id"]).first()
                processor = await self.get_processor(project, camera)

        await asyncio.sleep(0)
        result = await self.actuate_command(processor, camera, data)
        return result

    # save data into database

    async def actuate_command(self, processor, camera, data):

        # need to decision
        if "start" in data["action"]:
            if processor.state == "stop":
                processor.state = "start"
                processor.save()

        logger.debug(f"actuate command: {data}")
        if data.get("system"):
            processor_command = models.ProcessorCommand(
                processor=processor,
                action=data["action"],
                type="system",
            )
        else:
            processor_command = models.ProcessorCommand(
                processor=processor,
                action=data["action"],
                type="user",
            )
            if data.get("user_id"):
                user = models.User.objects(id=data["user_id"]).first()
                processor_command.owner = user

        processor.update_user_command(processor_command)
        processor_command.save()
        processor.save()

        compute_node = None
        try:
            compute_node = processor.compute_node
        except Exception as e:
            logger.exception(e)

        if data["action"] in ["start-recorder", "start-streamer"]:
            compute_node = await self.get_available_compute_node(compute_node)
            processor.compute_node = compute_node

        if not compute_node or not compute_node.is_online():
            if not compute_node:
                logger.debug("compute node is not available for start")
            elif not compute_node.is_online():
                logger.debug("compute node {compute_node.name} is not online")

            processor.state = "stop"
            processor.save()
            return False

        # need to decision
        processor_command.save()
        processor.save()

        # check starting process
        if "start" in data["action"] and processor.state == "start":
            processor.state = "starting"
        elif "stop" in data["action"] and processor.state != "stop":
            processor.state = "stopping"
        processor.save()

        command = dict(processor_id=str(processor.id), action=data["action"])
        if data["action"] in ["start-recorder", "start-streamer"]:
            command["attributes"] = dict(
                video_uri=camera.uri,
                fps=camera.frame_rate,
                size=(camera.width, camera.height),
                camera_id=str(camera.id),
                motion=data.get("motion", False),
                sensitivity=data.get("sensitivity", 0),
            )

        topic = "nokkhum.compute.{}.rpc".format(compute_node.mac)

        result = None
        result_data = dict(success=False)
        try:
            result = await self.nc.request(
                topic, json.dumps(command).encode(), timeout=60
            )
        except Exception as e:
            # logger.exception(e)
            processor_command.message = str(e)
            processor_command.completed = False
            processor_command.save()

            return False

        if result:
            result_data = json.loads(result.data.decode())
            processor_command.completed = True

        await self.update_status(processor)
        processor.save()
        # logger.debug(f"end {result_data}")
        processor_command.completed_date = datetime.datetime.now()
        processor_command.save()

        return True

    async def update_status(self, processor):
        command = dict(
            action="get-status",
            processor_id=str(processor.id),
        )

        try:
            topic = "nokkhum.compute.{}.rpc".format(processor.compute_node.mac)
            result = await self.nc.request(
                topic, json.dumps(command).encode(), timeout=60
            )
        except Exception as e:
            logger.exception(e)
            return

        result_data = json.loads(result.data.decode())

        checked = False

        if result_data["success"]:
            if result_data["state"] == "stop":
                processor.state = "stop"
                logger.debug(
                    f"compute node report processor {processsor.id} stop state"
                )

            for k, v in result_data["status"].items():
                checked = checked or v

        if not checked:
            processor.state = "stop"
        else:
            processor.state = "running"

    async def update_fail_processor(self, data, compute_node_id):
        # processor = self.get_processor(project, camera)
        # processor_id = next(iter(data['dead_process']))
        # logger.debug(next(iter(data['dead_process'])))
        # logger.debug('in update fail')
        compute_node = models.ComputeNode.objects.get(id=compute_node_id)
        for processor_id, msg in data["dead_process"].items():
            processor = models.Processor.objects.get(id=processor_id)
            fail_processor = models.FailRunningProcessor(
                processor=processor, compute_node=compute_node, message=msg
            )
            fail_processor.save()

            await self.command_controller.put_restart_processor_command(processor)
