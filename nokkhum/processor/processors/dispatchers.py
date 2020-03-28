import threading
import time

import cv2

import logging
logger = logging.getLogger(__name__)



class ImageDispatcher(threading.Thread):
    def __init__(self,
                 queue,
                 ):
        super().__init__()
        self.running = False
        self.input_queue = queue
        self.daemon = True
        self.active = False

        self.name = 'Image Dispatcher'

    def set_active(self):
        self.active = True

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        logger.debug('Start Image Dispatcher')

        while self.running:
            img = self.input_queue.get()
            if img is None:
                self.running = False
                break

            if not self.active:
                continue

        logger.debug('End Image Dispatcher')
