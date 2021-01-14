import asyncio
import logging
import pickle
import cv2

from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN

from nokkhum import models

logger = logging.getLogger(__name__)


class StreamingSubscriber:
    def __init__(self, queues, settings):
        self.settings = settings
        self.camera_queues = queues

    async def streaming_cb(self, msg):
        data = pickle.loads(msg.data)
        # logger.debug(data)
        queues = self.camera_queues.get(data["camera_id"])
        # if len(self.queues[data["camera_id"]])
        if not queues or len(queues) == 0:
            logger.debug(" no q in list")
            return
        logger.debug(f"len >>>>{len(queues)}")
        # self.queues[data["camera_id"]] = asyncio.queues.Queue(maxsize=30)
        img = cv2.imdecode(data["frame"], 1)
        byte_img = cv2.imencode(".jpg", img)[1].tobytes()

        for q in queues:
            if q.full():
                # logger.debug("drop image")
                q.get_nowait()
                await asyncio.sleep(0)

            await q.put(byte_img)

    async def set_up(self):
        logging.basicConfig(
            format="%(asctime)s - %(name)s:%(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.DEBUG,
        )

        # loop = asyncio.get_event_loop()
        # loop.set_debug(True)
        self.nc = NATS()
        self.nc._max_payload = 2097152
        # logger.debug("in setup")
        # logger.debug(f'>>>>{self.settings["NOKKHUM_MESSAGE_NATS_HOST"]}')

        await self.nc.connect(self.settings["NOKKHUM_MESSAGE_NATS_HOST"])

        self.sc = STAN()

        await self.sc.connect(
            self.settings["NOKKHUM_TANS_CLUSTER"], "streaming-sub", nats=self.nc
        )
        logger.debug("connected")

        live_streaming_topic = "nokkhum.streaming.cameras"
        self.stream_id = await self.sc.subscribe(
            live_streaming_topic, cb=self.streaming_cb
        )

    async def add_new_queue(self, camera_id):
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
