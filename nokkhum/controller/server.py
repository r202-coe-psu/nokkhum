import asyncio
import datetime
import json
import pathlib
import logging

logger = logging.getLogger(__name__)

from nats.aio.client import Client as NATS

from nokkhum import models

from . import compute_nodes
from . import processors
from . import commands
from . import results


class ControllerServer:
    def __init__(self, settings):
        self.settings = settings
        models.init_mongoengine(settings)

        
        self.nc = NATS()
        self.cn_report_queue = asyncio.Queue()
        self.processor_command_queue = asyncio.Queue()
        self.running = False
        self.cn_resource = compute_nodes.ComputeNodeResource()
        self.processor_controller = processors.ProcessorController(self.nc)
        self.command_controller = commands.CommandController(self.settings)
        self.result_controller = results.ResultController(self.settings)

    async def register_compute_node(self, data):
        response = self.cn_resource.update_machine_specification(data["machine"])
        return response
        # save compute node to database

    async def handle_compute_node_report(self, msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()

        # logger.debug("Received a rpc message on '{subject} {reply}': {data}".format(
        #         subject=subject, reply=reply, data=data))

        data = json.loads(data)
        if data["action"] == "register":
            response = await self.register_compute_node(data)
            await self.nc.publish(reply, json.dumps(response).encode())
            logger.debug(f'client {data["machine"]["name"]} is registed')
            return

        await self.cn_report_queue.put(data)

    async def handle_processor_command(self, msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()

        # logger.debug("Received a rpc message on '{subject} {reply}': {data}".format(
        #         subject=subject, reply=reply, data=data))
        data = json.loads(data)
        await self.processor_command_queue.put(data)

    async def process_expired_controller(self):
        while self.running:
            logger.debug("start process expired data")
            time_check = self.settings["DAIRY_TIME_TO_REMOVE"]
            hour, minute = time_check.split(":")
            date = datetime.date.today()
            time = datetime.time(int(hour), int(minute), 0)
            time_set = datetime.datetime.combine(date, time)
            time_to_check = time_set - datetime.datetime.now()

            # logger.debug(f'time to sleep {time_to_check.seconds}')
            await asyncio.sleep(time_to_check.seconds)
            self.command_controller.expired_processor_commands()

            await asyncio.sleep(1)
            self.result_controller.expired_video_records()

    async def handle_controller(self):
        while self.running:
            await asyncio.sleep(20)
            await self.command_controller.handle_controller_after_restart(
                self.processor_command_queue
            )

    # async def handle_
    async def process_compute_node_report(self):
        while self.running:
            data = await self.cn_report_queue.get()
            # logger.debug(f'process compute node: {data}')

            if data["action"] == "update-resource":
                self.cn_resource.update_machine_resources(
                    data["compute_node_id"], data["resource"]
                )
            elif data["action"] == "report-fail-processor":
                # logger.debug('pcnr: {}'.format(data))
                # logger.debug('>>>>>>> {}'.format(data['fail_processor_data']))
                await self.processor_controller.update_fail_processor(
                    data["fail_processor_data"],
                    data["compute_node_id"],
                    self.processor_command_queue,
                )
            elif data["action"] != "report":
                logger.debug("got unproccess report {}".format(str(data)))

            # process report command
            # await self.manager.update(data)

    async def process_processor_command(self):
        while self.running:
            data = await self.processor_command_queue.get()
            logger.debug(f"processor command: {data}")
           
            result = False
            try:
                result = await self.processor_controller.process_command(data)
            except Exception as e:
                logger.exception(e)
            
            if not result:
                logger.debug(f"process command fail, reentry command to queue")
                if 'start-recorder' == data['action']:
                    await asyncio.sleep(20)
                    await self.processor_command_queue.put(data)
                

    async def set_up(self, loop):
        await self.nc.connect(self.settings["NOKKHUM_MESSAGE_NATS_HOST"], loop=loop)
        logging.basicConfig(
            format="%(asctime)s - %(name)s:%(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.DEBUG,
        )

        report_topic = "nokkhum.compute.report"
        command_topic = "nokkhum.processor.command"

        cns_id = await self.nc.subscribe(
            report_topic, cb=self.handle_compute_node_report
        )
        ps_id = await self.nc.subscribe(command_topic, cb=self.handle_processor_command)

    def run(self):

        self.running = True
        loop = asyncio.get_event_loop()
        # loop.set_debug(True)
        loop.run_until_complete(self.set_up(loop))
        cn_report_task = loop.create_task(self.process_compute_node_report())
        processor_command_task = loop.create_task(self.process_processor_command())
        handle_expired_data_task = loop.create_task(self.process_expired_controller())
        handle_controller_task = loop.create_task(self.handle_controller())

        try:
            loop.run_forever()
        except Exception as e:
            print(e)
            self.running = False
            self.cn_report_queue.close()
            self.processor_command_queue.close()
            self.nc.close()
        finally:
            loop.close()
