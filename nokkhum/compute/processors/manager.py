'''
@author: boatkrap
'''

import threading
import queue
import json
import time

import logging
logger = logging.getLogger(__name__)


class ProcessPolling(threading.Thread):
    def __init__(self, processor, output_queue):
        super().__init__()
        self.processor = processor
        self.output_queue = output_queue
        self.running = True
        self.daemon = True

    def run(self):
        while self.running:
            if not self.processor.is_running():
                logger.debug(
                    'ProcessPolling processor id: {} terminate'.format(
                        self.processor.id))
                break

            data = self.processor.process.stdout.readline().decode('utf-8')
            logger.debug(f'data: {data}')
            if len(data) == 0 or data[0] != '{':
                time.sleep(0.1)
                continue
            data = data.strip()
            json_data = ''
            try:
                json_data = json.loads(data)
            except Exception as e:
                logger.exception(e)
                continue

            self.output_queue.put(json_data)


class ProcessorManager:

    def __init__(self):
        self.pool = dict()
        self.thread_pool = dict()
        self.output = dict()

    def add(self, processor_id, processor):
        if processor_id not in self.pool.keys():
            self.pool[processor_id] = processor
            self.output[processor_id] = queue.Queue()
            self.thread_pool[processor_id] = ProcessPolling(
                processor, self.output[processor_id])
            self.thread_pool[processor_id].start()

    def delete(self, processor_id):
        if processor_id in self.pool.keys():
            del self.pool[processor_id]

            self.thread_pool[processor_id].running = False
            self.thread_pool[processor_id].join()
            del self.thread_pool[processor_id]

            del self.output[processor_id]

    def get(self, processor_id):
        if processor_id in self.pool.keys():
            return self.pool[processor_id]
        else:
            return None

    def get_pool(self):
        return self.pool

    def list_processors(self):
        return self.pool.keys()

    def available(self):
        avialable_process = []
        for k, v in self.pool.items():
            if v.is_running():
                avialable_process.append(k)

        return avialable_process

    def read_process_output(self, processor_id):
        results = []
        counter = 0

        if processor_id not in self.pool.keys():
            return results

        q = self.output[processor_id]
        while q.qsize() > 0:
            message = q.get()
            results.append(message)
            counter += 1

            if counter > 100:
                break

        return results

    def remove_dead_process(self):
        dead_process = {}

        remove_process = [
            k for k, v in self.pool.items() if not v.is_running()]

        # try to remove dead process
        for key in remove_process:
            processor_process = self.pool[key]
            if not processor_process.is_running():
                result = ''
                try:
                    for line in processor_process.process.stdout:
                        result += line.decode('utf-8')
                    for line in processor_process.process.stderr:
                        result += line.decode('utf-8')
                except Exception as e:
                    logger.exception(e)

                if key in self.output:
                    if key in self.thread_pool:
                        self.thread_pool[key].running = False

                    while self.output[key].qsize() > 0:
                        result += '{}\n'.format(self.output[key].get())

                if len(result) == 0:
                    result = 'Process exist with Unknown Message'
                dead_process[key] = result
                self.delete(key)

        if len(dead_process) > 0:
            logger.debug('remove: %s', dead_process)
        return dead_process

    def get_pids(self):
        pids = []
        for k, v in self.pool.items():
            pids.append((v.process.pid, k))

        return pids
