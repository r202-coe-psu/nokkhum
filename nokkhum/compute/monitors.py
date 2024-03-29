"""
Created on Nov 2, 2011

@author: boatkrap
"""

import platform
import json

# import socket
# import multiprocessing
# import threading
import datetime
import time
import psutil
import asyncio
import copy

from . import machines

import logging

logger = logging.getLogger(__name__)


# class UpdateConfiguration:

#     def update(self, settings):
#         logger.debug('get variable: %s' % settings)
#         for variable in settings.keys():
#             config.Configurator.settings[variable] = settings[variable]


class ComputeNodeMonitor:
    def __init__(self, settings, processor_manager, publisher=None):

        self.settings = settings
        self.publisher = publisher
        self.processor_manager = processor_manager

        self.machine_specification = self.get_machine_specification()
        self.resource = self.get_resource()

    def set_publisher(self, publisher):
        self.publisher = publisher

    # def send_message(self, data):
    #     self.publisher.publish(
    #             'yana.compute.report',
    #             json.dumps(data).encode())

    def get_machine_specification(self):
        ms = machines.Machine(
            self.settings.get("NOKKHUM_PROCESSOR_RECORDER_PATH"),
            self.settings.get("NOKKHUM_COMPUTE_INTERFACE"),
        )

        return ms.get_specification()

    async def update_machine_specification(self):

        arguments = self.get_machine_specification()
        messages = {"method": "update_machine_specification", "args": arguments}
        logging.debug("update information: %s" % messages)

        return self.send_message(messages)

    async def get_resource(self):
        cpus = psutil.cpu_percent(interval=0.3, percpu=True)

        ms = self.machine_specification

        cpu_prop = dict(
            used=round(sum(cpus) / len(cpus)),
            used_per_cpu=cpus,
        )

        mem = psutil.virtual_memory()
        mem_prop = dict(total=mem.total, used=mem.used, free=mem.free)

        disk = psutil.disk_usage(self.settings.get("NOKKHUM_PROCESSOR_RECORDER_PATH"))
        disk_prop = dict(
            total=disk.total,
            used=disk.used,
            free=disk.free,
            percent=disk.percent,
        )

        processor_manager = self.processor_manager
        processor_list = []

        pcpu = 0
        pmem = 0

        # for pid, processor_id in processor_manager.get_pids():
        processor_pool = copy.copy(processor_manager.pool)
        for processor_id, processor in processor_pool.items():
            if not processor.is_running():
                continue
            pid = processor.process.pid
            try:
                process = psutil.Process(pid)
                process_status = dict(
                    pid=pid,
                    processor_id=processor_id,
                    num_threads=process.num_threads(),
                    cpu=process.cpu_percent(interval=0.2),
                    memory=process.memory_info().rss,
                    processors=processor.get_status(),
                    # messages=compute.processor_manager.read_process_output(processor_id)
                )
                pcpu += process_status["cpu"]
                pmem += process_status["memory"]

                processor_list.append(process_status)
            except Exception as e:
                logger.exception(e)
                logger.debug(
                    f"processor id {processor_id} or attribute {processor.attributes} fail, try to stop"
                )
                processor.stop()

            await asyncio.sleep(0)

        system_load = dict(
            cpu=sum(cpus) - pcpu if sum(cpus) - pcpu >= 0 else 0,
            memory=mem.used - pmem if mem.used - pmem >= 0 else 0,
        )

        resource = dict(
            name=platform.node(),
            cpu=cpu_prop,
            memory=mem_prop,
            disk=disk_prop,
            processors=processor_list,
            system_load=system_load,
            ip=ms["ip"],
            mac=ms["mac"],
            date=datetime.datetime.now().isoformat(),
        )

        # logging.debug('update resource: %s' % messages)

        return resource

    async def update_machine_resources(self):
        self.resource = await self.get_resource()
        messages = {"action": "update_resources", "resource": self.resource}
        return self.send_message(messages)

    async def get_processor_run_fail(self):
        logger.debug("try to remove dead process")
        processor_manager = self.processor_manager
        dead_process = processor_manager.remove_dead_process()
        if len(dead_process) == 0:
            return None
        logger.debug(f"dead >> {dead_process}")

        fail_processors = {
            "name": platform.node(),
            "ip": self.machine_specification["ip"],
            "mac": self.machine_specification["mac"],
            "dead_process": dead_process,
            "report_time": datetime.datetime.now().isoformat(),
        }

        logging.debug("camera_running_fail_report: %s" % messages)
        return fail_processors

    async def processor_running_fail_report(self):
        logger.debug("start processor running fail")
        arguments = await self.get_processor_run_fail()
        if arguments is None:
            return
        messages = {"method": "processor_run_fail_report", "args": arguments}
        return self.send_message(messages)

    async def check_resources(self):
        resource = await self.get_resource()

        old_cpu = self.resource["cpu"]["used"]
        current_cpu = resource["cpu"]["used"]

        if abs(old_cpu - current_cpu) > 20:
            self.resource = resource
            messages = {"method": "update_machine_resources", "args": resource}
            return self.send_message(messages)

        self.processor_running_fail_report()
