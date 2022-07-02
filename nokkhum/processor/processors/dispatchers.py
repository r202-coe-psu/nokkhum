import threading
import time
import asyncio
import cv2
import pickle
import logging
import json
from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN


logger = logging.getLogger(__name__)


class ImageDispatcher(threading.Thread):
    def __init__(
        self,
        queue,
        processor_id,
        camera_id,
        settings={},
        expected_frame_size=(640, 480),
        command_builder=None,
    ):
        super().__init__()
        self.name = "Image Dispatcher"

        self.running = False
        self.daemon = True
        self.active = False

        self.command_builder = command_builder

        self.input_queue = queue

        self.expected_frame_size = expected_frame_size
        self.processor_id = processor_id
        self.camera_id = camera_id
        self.settings = settings
        self.sc = None
        self.nc = None
        self.camera_topic = f"nokkhum.streaming.cameras.{camera_id}"

        # self.loop = asyncio.get_event_loop()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        self.publish_queue = asyncio.queues.Queue(maxsize=100)

    def stop(self):
        self.running = False

    async def set_up_message(self):
        self.nc = NATS()
        self.nc._max_payload = 2097152
        logger.debug(f'connect to nats {self.settings["NOKKHUM_MESSAGE_NATS_HOST"]}')
        await self.nc.connect(
            self.settings["NOKKHUM_MESSAGE_NATS_HOST"], io_loop=self.loop
        )

        logger.debug("2")
        # Start session with NATS Streaming cluster.
        self.sc = STAN()
        await self.sc.connect(
            self.settings["NOKKHUM_STAN_CLUSTER"],
            f"streaming-pub-{self.camera_id}",
            nats=self.nc,
        )

    async def tear_down_message(self):
        # await self.camera_topic_register.unsubscribe()
        # await self.camera_topic_remove.unsubscribe()
        await self.sc.close()
        await self.nc.close()
        self.sc = None
        self.nc = None

    async def publish_data(self, data):
        serialized_data = pickle.dumps(data)
        # logger.debug('public data')
        await self.sc.publish(
            self.camera_topic,
            serialized_data,
        )

    async def publish_frame(self):
        while self.running:
            if self.publish_queue.empty():
                await asyncio.sleep(0.01)
                # logger.debug(f'check status: {self.running}')
                continue

            data = await self.publish_queue.get()

            await self.publish_data(data)

    async def process_frame(self):
        # loop = asyncio.get_event_loop()
        # asyncio.set_event_loop(self.loop)
        while self.running:
            image = None
            if self.input_queue.empty():
                await asyncio.sleep(0.001)
                continue

            try:
                image = self.input_queue.get(timeout=1)
                if image is None:
                    self.running = False
                    continue
            except Exception as e:
                logger.exception(e)
                continue

            # if not self.active:
            #     await asyncio.sleep(0.001)
            #     continue

            # if self.camera_id not in self.camera_topics:
            #     await asyncio.sleep(0.001)
            #     continue

            # logger.debug(f"in dispatch {image.data}")
            if self.publish_queue.full():
                await self.publish_queue.get()
                logger.debug("public queue is full drop image")
                await asyncio.sleep(0.01)

            w, h = image.size()

            ratio = self.expected_frame_size[0] / w
            width = int(w * ratio)
            height = int(h * ratio)
            size = (width, height)
            image = cv2.resize(image.data, size)
            image_frame = cv2.imencode(".jpg", image)[1]
            data = dict(
                camera_id=self.camera_id,
                frame=image_frame,
            )

            await self.publish_queue.put(data)
            await asyncio.sleep(0)
            # need to await on publish
            # asyncio.run(self.sc.publish("nokkhum.streaming.live", data))
            # <----
            # asyncio.ensure_future(foo(loop))
        #     loop.run_until_complete(self.publish_frame(data))
        # asyncio.run(self.sc.publish("nokkhum.streaming.live", data))
        # self.loop.call_soon_threadsafe(self.publish_frame, data)
        # self.loop.create_task(self.sc.publish("nokkhum.streaming.live", data))
        # loop.close()

    def run(self):
        self.running = True
        logger.debug("Start Image Dispatcher")

        try:
            self.loop.run_until_complete(self.set_up_message())
            self.loop.create_task(self.publish_frame())
            self.loop.run_until_complete(self.process_frame())

            self.loop.run_until_complete(self.tear_down_message())
        except Exception as e:
            logger.exception(e)

        logger.debug("End Image Dispatcher")
