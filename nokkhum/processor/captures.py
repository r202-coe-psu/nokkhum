import cv2
import datetime
import copy
from .utils import Image

import logging

logger = logging.getLogger(__name__)


class VideoCapture:
    def __init__(
        self,
        video_uri,
        camera_id="cam",
    ):
        self.identifier = video_uri
        self.id = camera_id
        self.capture = None
        self.reconnect()

    def __del__(self):
        if self.capture:
            self.capture.release()

    def create_capture(self):
        uri = self.identifier
        logger.debug(f'uri --> {uri}')
        if type(uri) is str and "rtsp" in uri:
            gstreamer_uri = (
                f"rtspsrc location={uri} latency=30 ! decodebin"
                + " ! videoconvert ! appsink"
            )
            logger.debug(f'new uri --> {gstreamer_uri}')
            capture = cv2.VideoCapture(gstreamer_uri)
            if not capture.isOpened():
                capture = cv2.VideoCapture(uri)
        else:
            capture = cv2.VideoCapture(uri)

        # capture = cv2.VideoCapture(self.uri)
        if not capture.isOpened():
            logger.debug(f"could not open uri: {uri}")
            return False

        self.capture = capture
        logger.debug(
            f"open video capture {self.id} size: {self.get_size()} fps: {self.get_fps()}"
        )

        return True

    def get_fps(self):
        return self.capture.get(cv2.CAP_PROP_FPS)

    def get_size(self):
        if self.capture:
            return (
                self.capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT),
            )

        return (640, 480)

    def status(self):
        if self.capture is None:
            return False

        return self.capture.isOpened()

    def reconnect(self):
        if self.capture:
            self.capture.release()

        result = self.create_capture()

        logger.debug(f'create capture result {result}')
        if not result:
            raise Exception(f"camera cannot open {self.id}")

        logger.info("start capture camera: {}".format(self.id))

    def get_frame(self):
        ret, frame = self.capture.read()
        # cv2.imshow('video', frame)
        # cv2.waitKey(1)

        if not ret:
            raise Exception("could not get frame")

        return Image(frame)

    def stop(self):
        self.capture.release()
        self.capture = None
