import asyncio
import logging
import pickle
import cv2
import json
import queue
from nats.aio.client import Client as NATS
import threading

from concurrent.futures import ThreadPoolExecutor as PoolExecutor

# from concurrent.futures import ProcessPoolExecutor as PoolExecutor
from nokkhum import models


logger = logging.getLogger(__name__)


class StreamingSubscriber:
    def __init__(self, queues, settings):
        self.settings = settings
        models.init_mongoengine(settings)

        self.camera_queues = queues
        self.cameras_id_queue = asyncio.queues.Queue()
        self.image_queue = asyncio.queues.Queue()

        self.running = False
        self.stream_id = {}
        self.loop = asyncio.get_running_loop()
        self.pool = PoolExecutor(
            max_workers=settings.get("NOKKHUM_STREAMING_MAX_WORKER")
        )

    def process_message_data(self, message):
        data = pickle.loads(message)

        img = cv2.imdecode(data["frame"], 1)
        byte_img = cv2.imencode(".jpg", img)[1].tobytes()

        return data["camera_id"], byte_img

    async def put_image_to_queue(self):
        while self.running:
            if self.image_queue.empty():
                await asyncio.sleep(0.1)
                continue

            img = None
            try:
                future_result = await self.image_queue.get()
                while not future_result.done():
                    await asyncio.sleep(0.001)

                camera_id, img = future_result.result()
            except Exception as e:
                logger.exception(e)

            if not img:
                await asyncio.sleep(0)
                continue

            queues = self.camera_queues.get(camera_id)
            if not queues or len(queues) == 0:
                continue

            for q in queues:
                if q.full():
                    # logger.debug("drop image")
                    q.get_nowait()
                    await asyncio.sleep(0)

                await q.put(img)
        logger.debug("end live")

    async def receive_cb(self, msg):
        # self.message_queue.put(msg.data)
        # await msg.ack()
        result = self.loop.run_in_executor(
            self.pool, self.process_message_data, msg.data
        )
        await asyncio.sleep(0)
        await self.image_queue.put(result)

    async def disconnected_cb(self):
        logger.debug("disconnect")

    async def set_up(self):
        logging.basicConfig(
            format="%(asctime)s - %(name)s:%(lineno)d %(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.DEBUG,
        )

        logging.getLogger("asyncio").setLevel(logging.WARNING)

        # loop.set_debug(True)
        self.nc = NATS()
        self.nc._max_payload = 2097152
        # logger.debug("in setup")
        logger.debug(
            f'connect to nats server {self.settings["NOKKHUM_MESSAGE_NATS_HOST"]}'
        )

        await self.nc.connect(
            self.settings["NOKKHUM_MESSAGE_NATS_HOST"],
            max_reconnect_attempts=-1,
            reconnect_time_wait=2,
            disconnected_cb=self.disconnected_cb,
        )

        self.js = self.nc.jetstream()

        self.running = True
        loop = asyncio.get_event_loop()
        loop.create_task(self.put_image_to_queue())

    async def subscribe_camera_topic(self, camera_id):
        if camera_id in self.stream_id:
            logger.debug(f"found: {camera_id}")
            return

        live_streaming_topic = f"nokkhum.streaming.cameras.{camera_id}"

        try:
            stream_name = await self.js.find_stream_name_by_subject(
                live_streaming_topic
            )
            logger.debug(f"found stream name: {stream_name}")
            if stream_name:
                await self.js.delete_stream(f"streaming-camera-{camera_id}")
        except Exception as e:
            # logger.exception(e)
            logger.debug(f"not found stream name for: {live_streaming_topic}")

        await self.js.add_stream(
            name=f"streaming-camera-{camera_id}",
            subjects=[live_streaming_topic],
            max_age=1_000_000,
            max_msgs=10,
        )

        # print(check_stream)
        self.stream_id[camera_id] = await self.js.subscribe(
            live_streaming_topic,
            cb=self.receive_cb,
        )

    async def add_new_queue(self, camera_id, user_id):
        # make processors dict for check data processor if nor in processors dict send topic to controller
        if camera_id not in self.camera_queues:
            await self.subscribe_camera_topic(camera_id)
        q = asyncio.queues.Queue(maxsize=10)
        if user_id:
            user = models.User.objects.get(id=user_id)
            # logger.debug(user.get_fullname())
            camera = models.Camera.objects.get(id=camera_id)
            if not camera.project.is_member(user):
                return q
        await self.send_start_live(camera_id, user_id)

        queues = self.camera_queues.get(camera_id)
        if not queues:
            self.camera_queues[camera_id] = [q]
        else:
            self.camera_queues[camera_id].append(q)
        return q

    async def remove_queue(self, camera_id, user_id, queue):
        if camera_id in self.camera_queues and queue in self.camera_queues[camera_id]:
            self.camera_queues[camera_id].remove(queue)

        if len(self.camera_queues[camera_id]) == 0:
            # logger.debug("remove topic")
            await self.send_stop_live(camera_id, user_id)
            if camera_id in self.stream_id:
                try:
                    await self.js.delete_stream(f"streaming-camera-{camera_id}")
                except Exception as e:
                    logger.exception(e)

                self.stream_id.pop(camera_id)

            del self.camera_queues[camera_id]

    async def send_start_live(self, camera_id, user_id):
        # logger.debug("add_camera_topic")
        data = {"camera_id": camera_id, "user_id": user_id, "action": "start-streamer"}
        camera_register_topic = "nokkhum.processor.command"
        await self.nc.publish(camera_register_topic, json.dumps(data).encode())

    async def send_stop_live(self, camera_id, user_id):
        # logger.debug("remove_camera_topic")
        data = {"camera_id": camera_id, "user_id": user_id, "action": "stop-streamer"}
        camera_remove_topic = "nokkhum.processor.command"
        await self.nc.publish(camera_remove_topic, json.dumps(data).encode())
