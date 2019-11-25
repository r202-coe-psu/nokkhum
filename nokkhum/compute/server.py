import asyncio

import json
import datetime
import os
import pathlib

import logging
logger = logging.getLogger(__name__)

from nats.aio.client import Client as NATS
from nats.aio.errors import ErrTimeout

from . import machines
from . import monitors
from .processors import processor_controller

class ComputeNodeServer:
    def __init__(self, settings):
        self.settings = settings

        path = pathlib.Path(self.settings['NOKKHUM_PROCESSOR_RECORDER_PATH'])
        if not path.exists() and not path.is_dir():
            path.mkdir()
       
        machine = machines.Machine(
                storage_path=self.settings['NOKKHUM_PROCESSOR_RECORDER_PATH'],
                interface=self.settings['NOKKHUM_COMPUTE_INTERFACE'])
        self.machine_specification = machine.get_specification()
        self.mac_address = self.machine_specification.get('mac')

        self.processor_controller = processor_controller.ProcessorController()
        self.monitor = monitors.ComputeNodeMonitor(
                settings,
                self.processor_controller.processor_manager)
        self.running = False
        self.is_register = False
        self.id = 'compute node server'

    async def handle_rpc_message(self, msg):
        subject = msg.subject
        reply = msg.reply
        data = msg.data.decode()
        logger.debug("Received a rpc message on '{subject} {reply}': {data}".format(
            subject=subject, reply=reply, data=data))

        data = json.loads(data)
        action = data.get('action', None)

        if action == 'start':
            respons = self.processor_controller.start_processor(
                    data['processor_id'],
                    data['attributes'])
        elif action == 'stop':
            respons = self.processor_controller.stop_processor(
                    data['processor_id'])

        await self.nc.publish(reply, json.dumps(respons).encode())


    async def update_compute_node_resource(self):
        while self.running:
            await asyncio.sleep(20)
            # logger.debug('begin update resource')
            if not self.is_register:
                continue

            # need remove process
            # self.monitor.get_processor_run_fail()
            
            resource = self.monitor.get_resource()
            # logger.debug('start')
            response = dict(action='update-resource',
                            compute_node_id=self.id,
                            resource=resource,
                            date=datetime.datetime.now().isoformat())
            # logger.debug(f'response: {response}')
            await self.nc.publish(
                    'nokkhum.compute.report',
                    json.dumps(response).encode())
    
    
    async def update_fail_processor(self):
        while self.running:
            await asyncio.sleep(20)
            # logger.debug()
            fail_processor_data = self.monitor.get_processor_run_fail()
            # message = self.monitor.get_processor_run_fail()
            if fail_processor_data is None:
                continue

            response = dict(action='report-fail-processor',
                            compute_node_id=self.id,
                            fail_processor_data=fail_processor_data,
                            date=datetime.datetime.now().isoformat())
            # logger.debug('response : {}'.format(response))
            await self.nc.publish(
                    'nokkhum.compute.report',
                    json.dumps(response).encode())


    async def update_processor_output(self):
        processor_manager = self.processor_controller.processor_manager

        while self.running:
            is_sleep = True
            for pid in processor_manager.output.keys():
                results = processor_manager.read_process_output(pid)
                if len(results) == 0:
                    continue

                response = dict(action='report',
                                processor_id=pid,
                                results=results,
                                date=datetime.datetime.now().isoformat())

                await self.nc.publish(
                        'nokkhum.compute.report',
                        json.dumps(response).encode())

                if len(results) > 0:
                    is_sleep = False

            if is_sleep:
                await asyncio.sleep(1)

    async def set_up(self, loop):
        self.nc = NATS()
        await self.nc.connect(self.settings['NOKKHUM_MESSAGE_NATS_HOST'], loop=loop)
        
        logging.basicConfig(
                format='%(asctime)s - %(name)s:%(levelname)s - %(message)s',
                datefmt='%d-%b-%y %H:%M:%S',
                level=logging.DEBUG,
                )

        rpc_topic = 'nokkhum.compute.{}.rpc'.format(self.mac_address)
        logger.info('try to subscribe rpc topic: {}'.format(rpc_topic))
        rpc_sid = await self.nc.subscribe(
                rpc_topic,
                cb=self.handle_rpc_message)

 
        data = dict(action='register',
                    machine=self.machine_specification,
                    data=datetime.datetime.now().isoformat()
                    )

        while not self.is_register:
            logger.debug('Try to register compute node')
            try:
                response = await self.nc.request(
                        'nokkhum.compute.report',
                        json.dumps(data).encode(),
                        timeout=10
                        )
                self.is_register = True
                data = json.loads(response.data.decode())
                self.id = data['id']
            except Exception as e:
                logger.debug(e)

            if not self.is_register:
                await asyncio.sleep(1)


        logger.debug('Register success')

    def run(self):
        loop = asyncio.get_event_loop()
        # loop.set_debug(True)
        self.running = True
    
        loop.run_until_complete(self.set_up(loop))
        update_output_task = loop.create_task(self.update_processor_output())
        update_resource_task = loop.create_task(self.update_compute_node_resource())
        update_fail_processor_task = loop.create_task(self.update_fail_processor())
        
        try:
            loop.run_forever()
        except Exception as e:
            self.running = False
            self.processor_controller.stop_all()
            self.nc.close()
        finally:
            loop.close()
