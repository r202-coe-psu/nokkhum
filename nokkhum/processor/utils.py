import queue
import threading
import datetime

import logging
logger = logging.getLogger(__name__)


class Image:
    def __init__(self, data):
        self.data = data
        self.captured_date = datetime.datetime.now()

    def size(self):
        height, width, _ = self.data.shape
        return (width, height)


class ImageQueue(queue.Queue):
    def __init__(self, maxsize=50):
        super().__init__(maxsize=maxsize)

    def size(self):
        return self.queue.qsize()

    def put(self, data):
        # logger.info('{} queue size: {}'.format(
        #             threading.current_thread().name,
        #             self.queue.qsize()))
        if self.full():
            logger.info('{} queue drop image, queue size: {}'.format(
                    threading.current_thread().name,
                    self.qsize()))
            self.get()

        super().put(data)


    def stop(self):
        self.put(None)
        self.task_done()
