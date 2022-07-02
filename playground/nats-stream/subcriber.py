import cv2
import asyncio
from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN
import os
import logging

logger = logging.getLogger(__name__)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
import queue
import numpy as np
import pickle


class Subscriber:
    def __init__(self):
        self.q = queue.Queue()
        self.is_running = False

    async def run(self, loop):
        self.nc = NATS()
        await self.nc.connect("localhost:4222", io_loop=loop)

        # Start session with NATS Streaming cluster.
        self.sc = STAN()
        await self.sc.connect("test-cluster", "client-456", nats=self.nc)
        await self.sc.subscribe("nokkhum.streaming.processors", cb=self.handle_msg)

    async def handle_msg(self, msg):
        # print('cb topic')
        img = msg.data
        self.q.put(img)

    async def handle_q_cap(self):
        print("q cap")
        while self.is_running:
            if self.q.empty():
                print("q empty")
                await asyncio.sleep(1)
                continue
            print("have data in q")
            data = self.q.get()
            try:
                data = pickle.loads(data)
                print(data["processor_id"])
                img = data["frame"]
                cv2.imshow("live_camera", cv2.imdecode(img, 1))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            except Exception as e:
                print(e)

    def set_up(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run(loop))
        self.is_running = True
        handle_q = loop.create_task(self.handle_q_cap())
        try:
            loop.run_forever()
        except Exception as e:
            print(e)
        finally:
            self.is_running = False
            loop.close()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    ns = Subscriber()
    ns.set_up()
