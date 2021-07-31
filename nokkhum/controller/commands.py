from nokkhum import models
import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class CommandController:
    def __init__(self, settings, command_queue):
        self.settings = settings
        self.command_queue = command_queue

    async def remove_expired_processor_commands(self):
        days = self.settings["DUE_DATE"]
        lifetime_date = datetime.datetime.now() - datetime.timedelta(days=days)
        processor_commands = models.ProcessorCommand.objects(
            commanded_date__lt=lifetime_date,
            type="system",
        )
        processor_commands.delete()

    async def restart_processors(self):
        logger.debug("check and restart processor")
        accepted_date = datetime.datetime.now() - datetime.timedelta(seconds=120)
        pipeline = [
            {
                "$lookup": {
                    "from": "processor_commands",
                    "localField": "user_command.recorder.$id",
                    "foreignField": "_id",
                    "as": "recorder",
                }
            },
            {"$addFields": {"recorder": {"$arrayElemAt": ["$recorder", 0]}}},
            {"$match": {"recorder.action": "start-recorder"}},
        ]

        processors = models.Processor.objects(updated_date__lt=accepted_date).aggregate(
            pipeline
        )

        for p in processors:
            processor = models.Processor.objects(id=p["_id"]).first()
            await self.put_restart_processor_command(processor)

    async def put_restart_processor_command(self, processor):
        processor.state = "stop"
        processor.save()

        # try to restart
        if processor.count_system_start_recorder(600) > 30:
            logger.debug(f"stop restart processor id: {processor.id} many retry")
            return

        if "start" in processor.user_command.recorder.action:
            logger.debug(f"Try to restart processor id {processor.id}")
            data = {
                "action": processor.user_command.recorder.action,
                "camera_id": str(processor.camera.id),
                "processor_id": str(processor.id),
                "project_id": str(processor.project.id),
                "system": True,
            }
            if processor.camera.motion_property.active:
                data["motion"] = processor.camera.motion_property.active
                data["sensitivity"] = processor.camera.motion_property.sensitivity
            await self.command_queue.put(data)
