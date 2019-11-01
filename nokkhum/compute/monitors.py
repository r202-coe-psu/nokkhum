'''
Created on Nov 2, 2011

@author: boatkrap
'''

import platform
import json
# import socket
# import multiprocessing
# import threading
import datetime
import time
import psutil

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

    def send_message(self, data):
        self.publisher.publish(
                'yana.compute.report',
                json.dumps(data).encode())

    def get_machine_specification(self):
        ms = machines.Machine(
            self.settings.get('NOKKHUM_PROCESSOR_RECORDER_PATH'),
            self.settings.get('NOKKHUM_COMPUTE_INTERFACE')
        )

        return ms.get_specification()

    def update_machine_specification(self):

        arguments = self.get_machine_specification()
        messages = {'method': 'update_machine_specification', 'args': arguments}
        logging.debug('update information: %s' % messages)

        return self.send_message(messages)

    def get_resource(self):
        cpus = psutil.cpu_percent(interval=.3, percpu=True)

        ms = self.machine_specification

        cpu_prop = dict(
                used=round(sum(cpus) / len(cpus)),
                used_per_cpu=cpus,
                )

        mem = psutil.virtual_memory()
        mem_prop = dict(
                total=mem.total,
                used=mem.used,
                free=mem.free
                )

        disk = psutil.disk_usage(
                self.settings.get('NOKKHUM_PROCESSOR_RECORDER_PATH'))
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
        for pid, processor_id in processor_manager.get_pids():
            try:
                process = psutil.Process(pid)
                process_status = dict(
                    pid=pid,
                    processor_id=processor_id,
                    num_threads=process.num_threads(),
                    cpu=process.cpu_percent(interval=0.2),
                    memory=process.memory_info().rss,
                    # messages=compute.processor_manager.read_process_output(processor_id)
                    )
                pcpu += process_status['cpu']
                pmem += process_status['memory']

                processor_list.append(process_status)
            except Exception as e:
                logger.debug(e)

        system_load = dict(
                cpu=sum(cpus)-pcpu if sum(cpus)-pcpu >= 0 else 0,
                memory=mem.used-pmem if mem.used-pmem >= 0 else 0
            )

        resource = dict(
            name=platform.node(),
            cpu=cpu_prop,
            memory=mem_prop,
            disk=disk_prop,
            processors=processor_list,
            system_load=system_load,
            ip=ms['ip'],
            mac=ms['mac'],
            date=datetime.datetime.now().isoformat()
            )

        # logging.debug('update resource: %s' % messages)

        return resource

    def update_machine_resources(self):
        self.resource = self.get_resource()
        messages = {'action': 'update_resources', 'resource': self.resource}
        return self.send_message(messages)

    def get_processor_run_fail(self):
        processor_manager = self.processor_manager
        # logger.debug('try to remove dead process')
        dead_process = processor_manager.remove_dead_process()
        if len(dead_process) == 0:
            return None
        # logger.debug('dead>>{}'.format(dead_process))

        fail_processors = {
            'name': platform.node(),
            'ip': self.machine_specification['ip'],
            'mac': self.machine_specification['mac'],
            'dead_process': dead_process,
            'report_time': datetime.datetime.now().isoformat()
        }

#        logging.debug('camera_running_fail_report: %s' % messages)
        return fail_processors

    def processor_running_fail_report(self):
        arguments = self.get_processor_run_fail()
        if arguments is None:
            return
        messages = {'method': 'processor_run_fail_report', 'args': arguments}
        return self.send_message(messages)

    def check_resources(self):
        resource = self.get_resource()

        old_cpu = self.resource['cpu']['used']
        current_cpu = resource['cpu']['used']

        if abs(old_cpu - current_cpu) > 20:
            self.resource = resource
            messages = {'method': 'update_machine_resources', 'args': resource}
            return self.send_message(messages)

        self.processor_running_fail_report()


# class UpdateStatus(threading.Thread):

#     def __init__(self, publisher=None):
#         threading.Thread.__init__(self)
#         self.name = self.__class__.__name__
#         self._running = False
#         self.daemon = True
#         self._request_sysinfo = False
#         self.__s3thread = None

#         self.publisher = publisher
#         self.uinfo = UpdateInfomation(self.publisher)

#     def set_publisher(self, publisher):
#         self.publisher = publisher
#         self.uinfo.set_publisher(self.publisher)

#     def run(self):
#         time_to_sleep = 2
#         time_to_sent = 10

#         counter = 0
#         counter_sent = time_to_sent // time_to_sleep

#         update_status = False

#         self._running = True

#         logger.debug('start update')

#         while(self._running):
#             while not update_status:
#                 update_status = self.uinfo.update_machine_specification()
#                 if not update_status:
#                     logger.debug('wait message server %d second' %
#                                  time_to_sleep)
#                     time.sleep(time_to_sleep)

#             while(self._running):
#                 # logger.debug('request_sysinfo %s'%self._request_sysinfo)
#                 if self._request_sysinfo:
#                     self._request_sysinfo = False
#                     update_status = False
#                     # logger.debug('request_sysinfo -> break')
#                     break

#                 start_time = datetime.datetime.now()
#                 if counter == counter_sent:
#                     counter = 0
#                     try:
#                         self.uinfo.processor_running_fail_report()
#                     except Exception as e:
#                         logger.exception(e)

#                     try:
#                         self.uinfo.update_machine_resources()
#                     except Exception as e:
#                         logger.exception(e)

#                     # sync to s3 storage
#                     if config.Configurator.settings.get('nokkhum.storage.enable'):
#                         if config.Configurator.settings.get('nokkhum.storage.api') == 's3':
#                             self.push_s3 = True
#                         else:
#                             self.push_s3 = False
#                     else:
#                         self.uinfo.update_machine_specification()
#                         self.push_s3 = False

#                     if self.push_s3:
#                         if self.__s3thread is not None and not self.__s3thread.is_alive():
#                             self.__s3thread.join()
#                             self.__s3thread = None

#                         if self.__s3thread is None:
#                             self.__s3thread = s3.S3Thread()
#                             self.__s3thread.start()
#                 else:
#                     try:
#                         self.uinfo.check_resources()
#                     except Exception as e:
#                         logger.exception(e)

#                 end_time = datetime.datetime.now()

#                 delta = end_time - start_time
#                 sleep_time = time_to_sleep - delta.total_seconds()
#                 counter += 1
#                 if sleep_time > 0:
#                     time.sleep(sleep_time)

#         logger.debug(self.name + ' terminate')

#     def stop(self):
#         self._running = False

#     def get_machine_specification(self):
#         self._request_sysinfo = True
#         logger.debug('request_sysinfo: %s\n' % self._request_sysinfo)

