import asyncio

from nats.aio.client import Client as NATS

import flask
from flask import current_app

import threading
import asyncio
import atexit
import json


class MessageThread(threading.Thread):
    def __init__(self, app):
        super().__init__()
        self.deamon = True

        self.app = app
        self.running = False

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.queue = asyncio.Queue()

    def stop(self):
        self.running = False
        # self.loop.stop()

        # self.loop.run_until_complete(self.queue.put(None))

    def put_data(self, data):
        # self.loop.create_task(self.put_to_queue(data))
        try:
            self.queue.put_nowait(data)
        except Exception as e:
            print(e)
            # check for queue empty
            pass

    async def put_to_queue(self, data):
        await self.queue.put(data)

    async def initial_nats_client(self):
        self.nc = NATS()
        await self.nc.connect(current_app.config.get('NOKKHUM_MESSAGE_NATS_HOST'), self.loop)

    async def run_async_loop(self):
        await self.initial_nats_client()

        while self.running:
            data = None

            try:
                data = self.queue.get_nowait()
            except Exception as e:
                await asyncio.sleep(0.1)
                continue 

            if not data:
                continue

            msg = data.get('message', {})
            await self.nc.publish(data.get('topic'), json.dumps(msg).encode())

    def run(self):
        self.running = True
        with self.app.app_context():
            # self.loop.create_task(self.run_async_loop())
            # self.loop.run_forever()

            self.loop.run_until_complete(self.run_async_loop())

class NatsClient:
    def __init__(self, app=None):
        if app:
            self.init(app)

    def init_nats(self, app):
        message_thread = MessageThread(app)
        s = {"app": app, "thread": message_thread}
        app.extensions["nokkhum_nats"][self] = s
        message_thread.start()


    def init_app(self, app):
        self.app = app

        app.extensions = getattr(app, "extensions", {})

        if "nokkhum_nats" not in app.extensions:
            app.extensions["nokkhum_nats"] = {}

        @app.before_first_request
        def start_thread():


            if self in app.extensions["nokkhum_nats"]:
                self.stop()
            
            self.init_nats(app)

        atexit.register(self.stop)


    def stop(self):
        if self in self.app.extensions["nokkhum_nats"]:
            self.app.extensions["nokkhum_nats"][self]['thread'].stop()
        
    def publish(self, topic: str, message: str):
        t = self.app.extensions["nokkhum_nats"][self]['thread']
        t.put_data(dict(topic=topic, message=message))

nats_client = NatsClient()

def init_nats(app): 
    nats_client.init_app(app)

    # @app.before_first_request
    # def init_nats_client():
    #     with app.app_context():
    #         app.loop = None
    #         app.get_loop = get_loop
    #         app.get_nats_client = get_nats_client
   
