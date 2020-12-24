import threading
import time
import asyncio
import cv2
import pickle
import logging

logger = logging.getLogger(__name__)


class ImageDispatcher(threading.Thread):
    def __init__(self, queue, sc, processor_id, expected_frame_size=(640, 480)):
        super().__init__()
        self.running = False
        self.input_queue = queue
        self.daemon = True
        self.active = False
        self.sc = sc
        self.expected_frame_size = expected_frame_size
        self.name = "Image Dispatcher"
        self.processor_id = processor_id

    def set_active(self):
        self.active = True

    def stop(self):
        self.running = False

    async def publish_frame(self, data):
        await self.sc.publish("nokkhum.streaming.live", data)

    def run(self):
        self.running = True
        logger.debug("Start Image Dispatcher")
        # loop = asyncio.new_event_loop()
        # asyncio.set_event_loop(loop)
        while self.running:
            image = None
            try:
                image = self.input_queue.get(timeout=1)
                if image is None:
                    self.running = False
                    continue
            except Exception as e:
                logger.exception(e)
                pass

            if not self.active:
                continue
            logger.debug(f"in dispatch {image.data}")
            w, h = image.size()

            ratio = self.expected_frame_size[0] / w
            width = int(w * ratio)
            height = int(h * ratio)
            size = (width, height)
            image = cv2.resize(image.data, size)
            image_frame = cv2.imencode(".jpg", image)[1]
            data = {self.processor_id: image_frame}
            data = pickle.dumps(data)
            # need to await on publish
            # asyncio.run(self.sc.publish("nokkhum.streaming.live", data))
            # <----
            # asyncio.ensure_future(foo(loop))
        #     loop.run_until_complete(self.publish_frame(data))
        # loop.close()
        logger.debug("End Image Dispatcher")
