import cv2
import asyncio
from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN
import os
import logging
logger = logging.getLogger(__name__)
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"
import numpy as np
import pickle

class NatStream:
    async def run(self, loop):
        self.nc = NATS()
        await self.nc.connect('localhost:4223', io_loop=loop)

        # Start session with NATS Streaming cluster.
        self.sc = STAN()
        await self.sc.connect("test-cluster", "client-123", nats=self.nc)

    async def cap_camera(self):
        print('start cap')
        
        while(True):
            cap = cv2.VideoCapture('rtsp://admin:888888@172.30.222.194:10554/udp/av0_0')
            print('cap')
            if cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    cap.release()
                    print('reconnecting...')
                    continue
                frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
                retval, img  = cv2.imencode('.png', frame)
                #np_img = np.array(img, np.int8)
                # cv2.imshow('live_camera', cv2.imdecode(img,1))
                try:
                    await self.sc.publish("video.cap", pickle.dumps(img))
                except Exception as e:
                    print(e)
                # send data img.tobytes()

            
        cap.release()

    def set_up(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run(loop))

        cap_camera_task =  loop.create_task(self.cap_camera())
        try:
            loop.run_forever()
        except Exception as e:
            print(e)
        finally:
            loop.close()
            cv2.destroyAllWindows()

if __name__ == '__main__':
    ns = NatStream()
    ns.set_up()
            