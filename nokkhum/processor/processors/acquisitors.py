import threading
import datetime
import cv2
import time

import logging

logger = logging.getLogger(__name__)


class ImageAcquisitor(threading.Thread):
    def __init__(self, capture, queues, fps=None, size=None, command_builder=None):
        super().__init__()
        self.name = "ImageAcquisitor"
        self.running = False
        self.daemon = True
        self.name = "ImageAcquisition {}".format(capture.id)

        self.capture = capture
        self.queues = queues

        self.fps = None
        self.command_builder = command_builder

        if fps:
            self.fps = fps
        elif capture.get_fps() > 0:
            self.fps = capture.get_fps()

        if size:
            self.size = size
        else:
            self.size = capture.get_size()

    def reconnect_camera(self):
        self.capture.reconnect()
        while not self.capture.status():
            self.capture.reconnect()

            logger.error("waiting camera connect sleep 1s")
            if not self.running:
                break

            time.sleep(1)

    def resize_image(self, image):
        if self.size is None:
            return image

        width, height = image.size()

        if not width == self.size[0] or not height == self.size[1]:
            img = cv2.resize(image.data, self.size, interpolation=cv2.INTER_AREA)
            image.data = img

        return image

    def stop(self):
        self.running = False

    def run(self):
        logger.debug("Start ImageAcquisitor")
        self.running = True

        start_date = datetime.datetime.now()
        counter = 0
        drop_frame = -1
        checker = 0

        while self.running:
            try:
                image = self.capture.get_frame()
            except Exception as e:
                logger.exception(e)
                self.reconnect_camera()
                continue

            current_date = datetime.datetime.now()
            counter += 1

            if drop_frame > 0 and counter % drop_frame == 0:
                # print('drop', counter)
                continue

            checker += 1

            self.resize_image(image)
            # logger.debug(f'qsize {len(self.queues)}')
            for q in self.queues:
                q.put(image)

            if (current_date - start_date).seconds >= 1:
                # print('fps', self.fps)
                # print('counter', counter)
                # print('checker', checker)
                if self.fps and checker != self.fps:
                    result = counter - self.fps
                    # print('result', result)
                    if result > 0:
                        drop_frame = int(counter / result)
                        # print('reset drop frame', drop_frame)

                start_date = current_date
                counter = 0
                checker = 0

        logger.debug("End ImageAcquisitor")
