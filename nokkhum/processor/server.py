import pathlib
import argparse
import sys
import json
import threading
import time

import asyncio

from .utils import ImageQueue

from . import captures
from .processors import recorders
from .processors import acquisitors
from .processors import dispatchers
from .processors import detectors

import logging

logger = logging.getLogger(__name__)


class ProcessorServer:
    def __init__(self, settings):
        self.settings = settings
        self.running = False
        self.image_queues = []
        self.processors = {"live": None, "record": None, "acquisitor": None}

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
        logging.basicConfig(
            format="%(asctime)s - %(name)s:%(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.DEBUG,
        )

        path = pathlib.Path(options.directory)
        logger.debug(f"prepare directory {options.directory} is exists {path.exists()}")
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
                logger.debug(f"error {e}")
                continue

            if "action" in command:
                if command["action"] == "stop":
                    self.running = False

                elif command["action"] == "stop-live":
                    # self.running = False
                    if "live" in self.processors:
                        self.processors["live"].running = False
                        self.processors["live"].stop()

                elif command["action"] == "stop-record":
                    # self.running = False
                    if "record" in self.processors:
                        self.processors["record"].running = False
                        self.processors["record"].stop()

                if command.get("action") == "start-live":
                    self.processors["live"].set_active()
                    self.processors["live"].start()

                elif command.get("action") == "start-record":
                    self.processors["record"].start()

        logger.debug("End Commander")

    def run(self):

        self.running = True
        options = self.get_options()
        loop = asyncio.get_event_loop()

        self.setup(options)

        command = self.get_input()
        while command.get("action") not in ["start", "start-live", "start-record"]:
            command = self.get_input()

        recorder_queue = ImageQueue()
        self.image_queues.append(recorder_queue)

        dispatcher_queue = ImageQueue()
        self.image_queues.append(dispatcher_queue)

        # capture output queue default 2 queue
        # capture_output_queues = [recorder_queue, dispatcher_queue]
        capture_output_queues = [dispatcher_queue]

        if "motion" in command and command["motion"]:
            motion_queue = ImageQueue()
            self.image_queues.append(motion_queue)

            capture_output_queues = [motion_queue, dispatcher_queue]

            motion_detector = detectors.MotionDetector(
                input_queue=motion_queue, output_queues=[recorder_queue]
            )
            motion_detector.start()

        capture = captures.VideoCapture(
            command["video_uri"],
            options.processor_id,
        )

        acquisitor = acquisitors.ImageAcquisitor(
            capture=capture,
            queues=capture_output_queues,
            fps=command.get("fps", None),
            size=tuple(command.get("size", None)),
        )
        acquisitor.start()
        self.processors["acquisitor"] = acquisitor

        dispatcher = dispatchers.ImageDispatcher(
            dispatcher_queue,
            options.processor_id,
            command.get("camera_id"),
            self.settings,
        )
        self.processors["live"] = dispatcher

        if "motion" in command and command["motion"]:
            recorder = recorders.MotionVideoRecorder(
                queue=recorder_queue,
                directory=options.directory,
                processor_id=options.processor_id,
                fps=command.get("fps", capture.get_fps()),
                size=tuple(command.get("size", capture.get_size())),
                extension="mkv",
            )

        else:
            recorder = recorders.VideoRecorder(
                queue=recorder_queue,
                directory=options.directory,
                processor_id=options.processor_id,
                fps=command.get("fps", capture.get_fps()),
                size=tuple(command.get("size", capture.get_size())),
                extension="mkv",
            )
        self.processors["record"] = recorder

        if command.get("action") == "start-live":
            self.processors["live"].set_active()
            self.processors["live"].start()

        elif command.get("action") == "start-record":
            self.processors["record"].start()

        command_thread = threading.Thread(target=self.command_action, daemon=True)
        command_thread.start()

        # processors = [acquisitor, recorder, dispatcher]

        while self.running:
            try:
                time.sleep(1)
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
            if p:
                p.join()

        # capture.stop()
        # dispatcher.stop()
        command_thread.join(timeout=1)

        logger.debug("End server")
