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
        self.queues = queues

    async def streaming_cb(self, msg):
        data = pickle.loads(msg.data)

        queue = self.queues.get(data["processor_id"])
        if not queue:
            self.queues[data["processor_id"]] = asyncio.queues.Queue(maxsize=30)


        if queue.full():
            # print('drop image')
            queue.get_nowait()
        
        img = cv2.imdecode(data['frame'], 1)
        byte_img = cv2.imencode('.jpg', img)[1].tobytes()
        await queue.put(byte_img)


    async def set_up(self):
        # logging.basicConfig(
        #     format="%(asctime)s - %(name)s:%(levelname)s - %(message)s",
        #     datefmt="%d-%b-%y %H:%M:%S",
        #     level=logging.DEBUG,
        # )

        # loop = asyncio.get_event_loop()
        # loop.set_debug(True)
        self.nc = NATS()
        self.nc._max_payload = 2097152
        # logger.debug("in setup")
        # logger.debug(f'>>>>{self.settings["NOKKHUM_MESSAGE_NATS_HOST"]}')

        await self.nc.connect(self.settings["NOKKHUM_MESSAGE_NATS_HOST"])

        self.sc = STAN()

        await self.sc.connect(
                self.settings["NOKKHUM_TANS_CLUSTER"], "streaming-sub", nats=self.nc)
        logger.debug("connected")

        live_streaming_topic = "nokkhum.streaming.processors"
        self.stream_id = await self.sc.subscribe(live_streaming_topic, cb=self.streaming_cb)
    
