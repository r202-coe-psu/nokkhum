import threading
import cv2

import logging
logger = logging.getLogger(__name__)


class ImageAcquisitor(threading.Thread):
    def __init__(self, capture, queues):
        super().__init__()
        self.name = 'ImageAcquisitor'
        self.running = False
        self.daemon = True
        self.name = 'ImageAcquisition {}'.format(capture.id)

        self.capture = capture
        self.queues = queues

    def reconnect_camera(self):
        self.capture.reconnect()
        while(not self.capture.status()):
            self.capture.reconnect()

            logger.error("waiting camera connect sleep 1s")
            if not self.running:
                break

            time.sleep(1)

    def stop(self):
        self.running = False

    def run(self):
        logger.debug("Start ImageAcquisitor")
        self.running = True

        while self.running:
            try:
                image = self.capture.get_frame()
            except Exception as e:
                logger.exception(e)
                self.reconnect_camera()
                continue

            for q in self.queues:
                q.put(image)

        logger.debug("End ImageAcquisitor")
