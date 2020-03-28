import pathlib
import argparse
import sys
import json
import threading
import time
from .utils import ImageQueue

from . import captures
from .processors import recorders
from .processors import acquisitors
from .processors import dispatchers

import logging
logger = logging.getLogger(__name__)


class ProcessorServer:
    def __init__(self, settings):
        self.settings = settings
        self.running = False
        self.image_queues = []

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
        while command.get('action') != 'start':
            command = self.get_input()
        
        recorder_queue = ImageQueue()
        self.image_queues.append(recorder_queue)

        dispatcher_queue = ImageQueue()
        self.image_queues.append(dispatcher_queue)

        # capture output queue default 2 queue
        capture_output_queues = [recorder_queue, dispatcher_queue]

        # if 'motion' in command and command['motion']:
        #     motion_queue = ImageQueue()
        #     self.image_queues.append(motion_queue)

        #     capture_output_queue = [motion_queue, dispatcher_queue]

        capture = captures.VideoCapture(
                command['video_uri'],
                options.processor_id
                )

        acquisitor = acquisitors.ImageAcquisitor(
                capture=capture,
                queues=capture_output_queues
                )
        acquisitor.start()

        dispatcher = dispatchers.ImageDispatcher(dispatcher_queue)
        dispatcher.start()
                
        recorder = recorders.VideoRecorder(
                queue=recorder_queue,
                directory=options.directory,
                processor_id=options.processor_id,
                fps=command.get('fps', capture.get_fps()),
                size=tuple(command.get('size', capture.get_size()))
                )
        recorder.start()


        command_thread = threading.Thread(
                target=self.command_action,
                daemon=True)
        command_thread.start()

        processors = [acquisitor, recorder]

        while self.running:

            time.sleep(1)
            for p in processors:
                if p.running == False:
                    self.running = False
                    break

        capture.stop()
        for q in self.image_queues:
            q.stop()

        recorder.stop()
        dispatcher.stop()

        acquisitor.join()
        recorder.join()
        dispatcher.join()
        command_thread.join()
  
        logger.debug('End server') 
