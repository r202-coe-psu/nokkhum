import queue
import threading

import logging
logger = logging.getLogger(__name__)

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
