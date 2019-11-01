import cv2
from .base_camera import BaseCamera
import os
import datetime

import logging
logger = logging.getLogger(__name__)


class Camera(BaseCamera):
    def __init__(self, capture='gstreamer'):
        super().__init__()
        self.video_source = 0
        self.capture = capture

    # @staticmethod
    def set_video_source(self, source):
        self.video_source = source

    def create_video_capture(self):
        if self.capture == 'gstreamer':
            gstreamer_uri = 'rtspsrc location={} latency=30 ! decodebin'\
                    + ' ! videoconvert ! appsink'           
            camera = cv2.VideoCapture(
                    gstreamer_uri.format(self.video_source),
                    cv2.CAP_GSTREAMER)

            print(f'=> gstreamer {camera.isOpened()}')
        else:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
            camera = cv2.VideoCapture(self.video_source)
            print(f'=> ffmpeg {camera.isOpened()}')
        
        print(f'=> first time open {camera.isOpened()}')
        if not camera.isOpened():
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
            camera = cv2.VideoCapture(self.video_source)

        logger.debug(f'source: {self.video_source}')
        if not camera.isOpened():
            print('Could not start camera.')
            camera.release()
            return None
            # raise RuntimeError('Could not start camera.')

        return camera


    # @staticmethod
    def frames(self):
        camera = self.create_video_capture()
        if not camera:
            return

        while self.running:
            # read current frame
            ret, img = camera.read()
            if not ret:
                camera.release()
                print('reconnecting...')
                camera = self.create_video_capture()
                if not camera:
                    break
            try:
                img = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
            except Exception as e:
                print('error', e)
                continue

            # encode as a jpeg image and return it
            yield cv2.imencode('.jpg', img)[1].tobytes()

        if camera:
            camera.release()
