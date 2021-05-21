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
        counter = 0
        self.capture.close()
        logger.debug('reconnect camera')
        while not self.capture.status():
            try:
                self.capture.reconnect()
            except Exception as e:
                logger.exception(e)
            counter += 1
            
            if counter > 10:
                self.running = False

            if not self.running:
                logger.debug('Try to open many time')
                break

            logger.debug(f"waiting camera connect sleep 1s counter {counter}")
            time.sleep(1)
        logger.debug('reconnect camera success')

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

        while self.running:
            try:
                image = self.capture.get_frame()
            except Exception as e:
                logger.exception(e)
                self.reconnect_camera()
                continue

            current_date = datetime.datetime.now()
            counter += 1

            if drop_frame == 0 or counter % drop_frame != 0:
                self.resize_image(image)
                # logger.debug(f'qsize {len(self.queues)}')
                for q in self.queues:
                    q.put(image)

            # drop frame hear
            # else:
            #     logger.debug(f'df {drop_frame} counter {counter} fps {self.fps} drop')

            if (current_date - start_date).seconds >= 1:
                # print('fps', self.fps)
                # print('counter', counter)
                drop_frame = 0
                if self.fps and counter >= self.fps:
                    result = counter - self.fps
                    # print('result', result)
                    if result > 0:
                        drop_frame = round(counter / result)
                        # print('reset drop frame', drop_frame)

                start_date = current_date
                counter = 0


                for q in self.queues:
                    if q.full():
                        logger.debug("Queue is full try to sleep")
                        time.sleep(0.1)

        logger.debug("End ImageAcquisitor")
