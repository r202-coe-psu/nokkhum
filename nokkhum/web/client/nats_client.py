import asyncio

from nats.aio.client import Client as NATS

import flask
from flask import current_app

import threading
import asyncio
import atexit
import json
import time
import queue


class NatsClient:
    def __init__(self, app=None):
        if app:
            self.init_app(app)

        self.app = app
        self.nc = None
        self.loop = asyncio.new_event_loop()

    def init_nats(self, app):

        self.nc = NATS()
        if not self.loop or self.loop.is_running:
            self.loop = asyncio.new_event_loop()

        self.loop.run_until_complete(
            self.nc.connect(
                app.config.get("NOKKHUM_MESSAGE_NATS_HOST"),
                max_reconnect_attempts=-1,
                reconnect_time_wait=2,
            )
        )

    def init_app(self, app):
        self.app = app

        @app.before_first_request
        def init_nats_client():
            print("init nats client")
            self.init_nats(self.app)
            print("end init nats client")

    def stop(self):
        if self.nc:
            self.nc.close()
        if self.loop:
            self.loop.close()

    def get_loop(self):
        if not self.loop.is_running():
            self.init_nats(self.app)

        return self.loop

    def publish(self, topic: str, message: dict):
        loop = self.get_loop()
        loop.run_until_complete(self.nc.publish(topic, json.dumps(message).encode()))

    def request(self, topic: str, message: dict):
        return message
        loop = self.get_loop()

        msg = loop.run_until_complete(
            self.nc.request(topic, json.dumps(message).encode(), timeout=1)
        )
        return json.loads(msg.data.decode())


nats_client = NatsClient()
