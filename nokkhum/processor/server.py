import pathlib
import argparse
import sys
import json
import threading
import time

import asyncio

from .utils import ImageQueue

from . import captures
from . import commands

from .processors import recorders
from .processors import acquisitors
from .processors import dispatchers
from .processors import detectors

import logging
from logging import handlers

logger = logging.getLogger(__name__)


class ProcessorServer:
    def __init__(self, settings):
        self.settings = settings
        self.running = False
        self.processors = {"video-streamer": None, "video-recorder": None, "acquisitor": None}

        self.image_queues = []
        self.capture_output_queues = []

        self.command_builder = commands.CommandBuilder()

    def get_options(self):
        parser = argparse.ArgumentParser(description="Nokkhum Recorder")
        parser.add_argument(
            "--directory",
            dest="directory",
            default="/tmp",
            help="set directory for storing video footage, defaul is /tmp.",
        )
        parser.add_argument(
            "--processor_id",
            dest="processor_id",
            default="processor",
            help="identify processor_id",
        )

        return parser.parse_args()

    def setup(self, options):

        path = pathlib.Path(options.directory) / options.processor_id / 'log'
        if not path.exists():
            path.mkdir(parents=True)

        # logging.basicConfig(
        #     format="%(asctime)s - %(name)s:%(levelname)s - %(message)s",
        #     datefmt="%d-%b-%y %H:%M:%S",
        #     level=logging.DEBUG,
        # )

        handler = handlers.TimedRotatingFileHandler(
                f'{path}/processor.log',
                'midnight',
                1,
                backupCount=10)
        formatter = logging.Formatter('%(asctime)s %(name)s:%(lineno)d %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)

        logger.debug('setup finish')

    def get_input(self):
        data = input().strip()
        while len(data) == 0:
            data = input().strip()

        return json.loads(data)

    def command_action(self):
        logger.debug("Start Commander")
        while self.running:
            try:
                command = self.get_input()
                logger.debug(f'get command {command}')
            except Exception as e:
                logger.debug(f"error {e}")
                continue

            if "action" in command:

                if command.get("action") == "start-acquisitor":
                    self.init_acquisitor(command)
                elif command.get("action") == "start-streamer":
                    self.init_dispatcher(command)
                    # self.processors["video-streamer"].set_active()
                elif command.get("action") == "start-recorder":
                    self.init_recorder(command)

                elif command["action"] == "stop":
                    self.running = False
                    for p in self.processors.values():
                        if p:
                            p.stop()
                elif command["action"] == "stop-streamer":
                    if self.processors["video-streamer"]:
                        # self.processors["video-streamer"].stop()
                        self.stop_dispatcher()
                elif command["action"] == "stop-recorder":
                    if self.processors["video-recorder"]:
                        self.processors["video-recorder"].stop()

                elif command.get('action') == 'get-status':
                    data = dict()
                    for k, v in self.processors.items():
                        if v and v.running:
                            data[k] = True
                        else:
                            data[k] = False
                    print(json.dumps(data))

        logger.debug("End Commander")

    def init_acquisitor(self, command):
        if 'acquisitor' in self.processors and \
                self.processors['acquisitor'] and \
                self.processors["acquisitor"].is_alive():
            return

        # capture output queue default 2 queue
        # capture_output_queues = [recorder_queue, dispatcher_queue]
        # capture_output_queues = [dispatcher_queue]

        fps=command.get("fps", self.settings.get('NOKKHUM_PROCESSOR_ACQUISITOR_DEFAULT_FPS'))
        size=tuple(command.get("size", self.settings.get('NOKKHUM_PROCESSOR_ACQUISITOR_DEFAULT_SIZE')))


        capture = None
        try:
            capture = captures.VideoCapture(
                command["video_uri"],
                # options.processor_id,
                command['camera_id'],
            )
        except Exception as e:
            logger.exception(e)
            self.running = False
            return


        
        acquisitor = acquisitors.ImageAcquisitor(
            capture=capture,
            queues=self.capture_output_queues,
            fps=fps,
            size=size,
            command_builder=self.command_builder,
        )
        acquisitor.start()
        self.processors["acquisitor"] = acquisitor



    def init_recorder(self, command):

        is_motion = command.get('motion', False)
        if 'video-recorder' in self.processors and \
                self.processors["video-recorder"]  and \
                self.processors["video-recorder"].is_alive():
            return
        recorder_queue = ImageQueue()
        self.image_queues.append(recorder_queue)
        self.capture_output_queues.append(recorder_queue)

        fps=command.get("fps", 0)
        if fps == 0 and self.processors["acquisitor"]:
            fps = self.processors["acquisitor"].fps
        size=tuple(command.get("size", []))
        if size == tuple([]):
            size = self.processors["acquisitor"].size

        if is_motion:
            motion_queue = ImageQueue()
            self.image_queues.append(motion_queue)

            capture_output_queues = [motion_queue, dispatcher_queue]

            motion_detector = detectors.MotionDetector(
                input_queue=motion_queue, output_queues=[recorder_queue]
            )
            motion_detector.start()


            recorder = recorders.MotionVideoRecorder(
                queue=recorder_queue,
                directory=self.options.directory,
                processor_id=self.options.processor_id,
                fps=fps,
                size=size,
                extension="mkv",
                command_builder=self.command_builder,
            )

        else:
            recorder = recorders.VideoRecorder(
                queue=recorder_queue,
                directory=self.options.directory,
                processor_id=self.options.processor_id,
                fps=fps,
                size=size,
                extension="mkv",
                command_builder=self.command_builder,
            )
        recorder.start()
        self.processors["video-recorder"] = recorder


    def init_dispatcher(self, command):
        if 'video-streamer' in self.processors and \
                self.processors["video-streamer"] and \
                self.processors["video-streamer"].is_alive():
            return

        dispatcher_queue = ImageQueue()
        self.image_queues.append(dispatcher_queue)
        self.capture_output_queues.append(dispatcher_queue)
        dispatcher = dispatchers.ImageDispatcher(
            dispatcher_queue,
            self.options.processor_id,
            command.get("camera_id"),
            self.settings,
            command_builder=self.command_builder,
        )
        dispatcher.start()
        self.processors["video-streamer"] = dispatcher


    def stop_dispatcher(self):
        if 'video-streamer' in self.processors and \
                self.processors["video-streamer"] is None:
            return

        processor = self.processors["video-streamer"]

        # logger.debug(f'q size {len(self.image_queues)}')
        input_queue = processor.input_queue
        self.capture_output_queues.remove(input_queue)
        self.image_queues.remove(input_queue)
        
        processor.stop()
        processor.join()
        self.processors["video-streamer"] = None


        # logger.debug(f'q size {len(self.image_queues)}')


    def run(self):

        self.running = True
        options = self.get_options()
        loop = asyncio.get_event_loop()

        self.setup(options)
        self.options = options

        # command = self.get_input()
        # while command.get("action") not in ["start", "start-live", "start-record"]:
        #     command = self.get_input()


        # if command.get("action") == "start-live":
        #     self.processors["live"].set_active()
        #     self.processors["live"].start()

        # elif command.get("action") == "start-record":
        #     self.processors["record"].start()

        command_thread = threading.Thread(target=self.command_action, daemon=True)
        command_thread.start()

        # processors = [acquisitor, recorder, dispatcher]

        while self.running:
            try:
                time.sleep(1)
                if self.processors["acquisitor"] and not self.processors["acquisitor"].running:
                    self.running = False
            except KeyboardInterrupt as e:
                logger.exception(e)
                self.running = False
                break
            except Exception as e:
                logger.exception(e)
                self.running = False
                break

            # for p in processors:
            #     if p.running == False:
            #         self.running = False
            #         break

        for p in self.processors.values():
            if p and p.is_alive():
                p.stop()

        for q in self.image_queues:
            q.stop()

        for p in self.processors.values():
            if p and p.is_alive():
                p.join()

        # capture.stop()
        # dispatcher.stop()
        command_thread.join(timeout=1)

        logger.debug("End server")
