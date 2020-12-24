import asyncio
from nokkhum import models
from nats.aio.client import Client as NATS
from stan.aio.client import Client as STAN
import logging

logger = logging.getLogger(__name__)


class StreamingSubscriber:
    def __init__(self, settings):
        self.settings = settings
        models.init_mongoengine(settings)

    async def streaming_cb(self, msg):
        logger.debug(msg)

    async def set_up(self, loop):
        logging.basicConfig(
            format="%(asctime)s - %(name)s:%(levelname)s - %(message)s",
            datefmt="%d-%b-%y %H:%M:%S",
            level=logging.DEBUG,
        )
        self.nc = NATS()
        self.nc._max_payload = 2097152
        logger.debug("in setup")
        logger.debug(f'>>>>{self.settings["NOKKHUM_MESSAGE_NATS_HOST"]}')
        await self.nc.connect(self.settings["NOKKHUM_MESSAGE_NATS_HOST"], loop=loop)
        self.sc = STAN()
        await self.sc.connect(
            self.settings["NOKKHUM_TANS_CLUSTER"], "streaming-sub", nats=self.nc
        )

        live_streaming_topic = "nokkhum.streaming.live"
        # command_topic = "nokkhum.processor.command"

        # cns_id = await self.nc.subscribe(
        #     report_topic, cb=self.handle_compute_node_report
        # )
        # ps_id = await self.nc.subscribe(command_topic, cb=self.handle_processor_command)
        self.stream_id = await self.sc.subscribe(
            live_streaming_topic, cb=self.streaming_cb
        )

    def run(self):

        self.running = True
        loop = asyncio.get_event_loop()
        # loop.set_debug(True)
        loop.run_until_complete(self.set_up(loop))
        # cn_report_task = loop.create_task(self.process_compute_node_report())
        # processor_command_task = loop.create_task(self.process_processor_command())
        # handle_expired_data_task = loop.create_task(self.process_expired_controller())
        # handle_controller_task = loop.create_task(self.handle_controller())

        try:
            loop.run_forever()
        except Exception as e:
            print(e)
            self.running = False
            # self.cn_report_queue.close()
            # self.processor_command_queue.close()
            self.nc.close()
        finally:
            loop.close()
