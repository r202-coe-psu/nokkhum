import threading
import time

import cv2

import logging
logger = logging.getLogger(__name__)


class VideoCapture(threading.Thread):
    def __init__(self, uri, queues=[]):
        super().__init__()
        self.uri = uri
        self.running = False
        self.queues = queues
        self.capture = None
        self.daemon = True

    def create_capture(self):

        uri = self.uri
        if 'rtsp' in self.uri:
            uri = f'rtspsrc location={uri} latency=30 ! decodebin ! videoconvert ! appsink'
            capture = cv2.VideoCapture(uri, cv2.CAP_GSTREAMER)
        else:
            capture = cv2.VideoCapture(uri)
        # capture = cv2.VideoCapture(self.uri)

        if not capture.isOpened():
            self.running = False
            logger.debug(f'cloud not open uri: {self.uri}')
            return None

        self.capture = capture

    def get_fps(self):
        return self.capture.get(cv2.CAP_PROP_FPS)

    def get_size(self):
        if self.capture:
            return (self.capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                    self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (640, 480)

    def stop(self):
        self.running = False

    def run(self):
        self.running = True
        self.create_capture()

        while self.running:
            if self.capture is None or not self.capture.isOpened():
                self.running = False
                break

            ret, image = self.capture.read()

            if not ret:
                self.running = False
                break
            
            for q in self.queues:
                q.put(image)

        if not self.capture is None:
            self.capture.release()
        logger.debug('End Video Capture')
