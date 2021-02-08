import asyncio
import logging
import pickle
import cv2
import json
import queue
from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN
import threading

from nokkhum import models

logger = logging.getLogger(__name__)


class ImageProcessor(threading.Thread):
    def __init__(self, input_queue, output_queue):
        super().__init__()
        self.running = False
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        self.running = True

        while self.running:
            msg = self.input_queue.get()
            data = pickle.loads(msg)


            img = cv2.imdecode(data["frame"], 1)
            byte_img = cv2.imencode(".jpg", img)[1].tobytes()

            self.output_queue.put(
                    (data["camera_id"], byte_img)
                    )


class StreamingSubscriber:
    def __init__(self, queues, settings):
        self.settings = settings
        self.camera_queues = queues
        self.cameras_id_queue = asyncio.queues.Queue()
        self.message_queue = queue.Queue()
        self.image_queue = queue.Queue()

        self.running = False
        self.stream_id = {}

        self.loop = asyncio.get_event_loop()
        self.image_processor = ImageProcessor(
                self.message_queue,
                self.image_queue,
                )

        self.image_processor.start()


    async def put_image_to_queue(self):
        while self.running:
            if self.image_queue.empty():
                await asyncio.sleep(0.001)
                continue

            camera_id, img = self.image_queue.get()

            queues = self.camera_queues.get(camera_id)
            if not queues or len(queues) == 0:
                return

            if not img:
                await asyncio.sleep(0.001)
                continue

            for q in queues:
                if q.full():
                    logger.debug("drop image")
                    q.get_nowait()
                    await asyncio.sleep(0)
                
                await q.put(img)


    async def streaming_cb(self, msg):
        self.message_queue.put(msg.data)


    async def disconnected_cb(self):
        logger.debug("disconnect")


    async def set_up(self):
        logging.basicConfig(
            format="%(asctime)s - %(name)s:%(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.DEBUG,
        )

        logging.getLogger("asyncio").setLevel(logging.WARNING)

        # loop.set_debug(True)
        self.nc = NATS()
        self.nc._max_payload = 2097152
        # logger.debug("in setup")
        # logger.debug(f'>>>>{self.settings["NOKKHUM_MESSAGE_NATS_HOST"]}')

        await self.nc.connect(
            self.settings["NOKKHUM_MESSAGE_NATS_HOST"],
            disconnected_cb=self.disconnected_cb,
        )

        self.sc = STAN()

        await self.sc.connect(
            self.settings["NOKKHUM_TANS_CLUSTER"],
            "streaming-sub",
            nats=self.nc,
        )
        # logger.debug("connected")

        self.running = True
        loop = asyncio.get_event_loop()
        loop.create_task(self.put_image_to_queue())
        

        # try:
        # loop.run_forever()
        # except Exception as e:
        #     loop.close()
        # finally:
        #     self.running = False
        #     loop.close()

    async def subscribe_camera_topic_error(self, error):
        print(f'error sub {error}')


    async def subscribe_camera_topic(self, camera_id):
        live_streaming_topic = f"nokkhum.streaming.cameras.{camera_id}"
        self.stream_id[camera_id] = await self.sc.subscribe(
            live_streaming_topic,
            cb=self.streaming_cb,
            error_cb=self.subscribe_camera_topic_error,
        )


    async def add_new_queue(self, camera_id):
        # make processors dict for check data processor if nor in processors dict send topic to controller
        if camera_id not in self.camera_queues:
            await self.subscribe_camera_topic(camera_id)
        await self.register_camera_topic(camera_id)

        queues = self.camera_queues.get(camera_id)
        q = asyncio.queues.Queue(maxsize=10)
        if not queues:
            self.camera_queues[camera_id] = [q]
        else:
            self.camera_queues[camera_id].append(q)
        return q


    async def remove_queue(self, camera_id, queue):
        if camera_id in self.camera_queues and queue in self.camera_queues[camera_id]:
            self.camera_queues[camera_id].remove(queue)

        if len(self.camera_queues[camera_id]) == 0:
            # logger.debug("remove topic")
            await self.stream_id[camera_id].unsubscribe()
            del self.camera_queues[camera_id]
            await self.remove_camera_topic(camera_id)
            # logger.debug("success")


    async def register_camera_topic(self, camera_id):
        # logger.debug("add_camera_topic")
        data = {"camera_id": camera_id}
        camera_register_topic = "nokkhum.streaming.cameras.register"
        await self.nc.publish(camera_register_topic, json.dumps(data).encode())


    async def remove_camera_topic(self, camera_id):
        # logger.debug("remove_camera_topic")
        data = {"camera_id": camera_id}
        camera_remove_topic = "nokkhum.streaming.cameras.remove"
        await self.nc.publish(camera_remove_topic, json.dumps(data).encode())
