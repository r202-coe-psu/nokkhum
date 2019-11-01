import pathlib
import argparse
import sys
import queue
import json
import threading
import time

from . import recorders
from . import videos

import logging
logger = logging.getLogger(__name__)

class ImageQueue:
    def __init__(self, maxsize=50):
        self.queue = queue.Queue(maxsize=maxsize)

    def put(self, data):
        if self.queue.full():
            self.queue.get()
            logger.debug('Drop image')
            time.sleep(0.1)

        self.queue.put(data)

    def get(self):
        return self.queue.get()

    def stop(self):
        self.queue.put(None)
        self.queue.task_done()


class ProcessorServer:
    def __init__(self, settings):
        self.settings = settings
        self.image_queue = ImageQueue()
        self.running = False

    def get_options(self):
        parser = argparse.ArgumentParser(description='Nokkhum Recorder')
        parser.add_argument(
                '--directory',
                dest='directory',
                default='/tmp',
                help='set directory for storing video footage, defaul is /tmp.')
        parser.add_argument(
                '--processor_id',
                dest='processor_id',
                default='processor',
                help='identify processor_id')

        return parser.parse_args()

    def setup(self, options):
        logging.basicConfig(
                format='%(asctime)s - %(name)s:%(levelname)s - %(message)s',
                datefmt='%d-%b-%y %H:%M:%S',
                level=logging.DEBUG,
                )

        path = pathlib.Path(options.directory)
        logger.debug(f'prepare directory {options.directory} is exists {path.exists()}')

        if not path.exists():
            path.mkdir(parents=True)

    def get_input(self):
        data = input().strip()
        while len(data) == 0:
            data = input().strip()

        return json.loads(data)

    def command_action(self):
        while self.running:
            try:
                command = self.get_input()
            except Exception as e:
                logger.debug(f'error {e}')
                continue

            if 'action' in command:
                if command['action'] == 'stop':
                    self.running = False
        
        logger.debug('End Commander')

    def run(self):
       
        self.running = True
        options = self.get_options()

        self.setup(options)

        command = self.get_input()

        capture = videos.VideoCapture(command['video_uri'], queues=[self.image_queue])
        capture.start()

        recorder = recorders.VideoRecorder(
                queue=self.image_queue,
                directory=options.directory,
                processor_id=options.processor_id,
                fps=command.get('fps'),
                size=tuple(command.get('size', capture.get_size()))
                )
        recorder.start()

        command_thread = threading.Thread(
                target=self.command_action,
                daemon=True)
        command_thread.start()

        processors = [capture, recorder]

        while self.running:

            time.sleep(1)
            for p in processors:
                if p.running == False:
                    self.running = False
                    break

        capture.stop()
        self.image_queue.stop()
        recorder.stop()

        capture.join()
        recorder.join()
        # command_thread.join()
  
        logger.debug('End server') 
