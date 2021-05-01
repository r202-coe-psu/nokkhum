import asyncio
from quart import (
    Blueprint,
    Response,
    g,
    make_response,
    current_app,
    stream_with_context,
)

import logging
import datetime

module = Blueprint("live_streaming", __name__, url_prefix="/live")
logger = logging.getLogger(__name__)


TIMEOUT = 30

async def generate_frame(camera_id, ss):
    queue = await ss.add_new_queue(camera_id)

    served_date = datetime.datetime.now()
    running = True
    try:
        logger.debug(f"{camera_id} is live")
        while running:
            now = datetime.datetime.now()
            if queue.empty():
                await asyncio.sleep(0.1)

                # logger.debug(f"{camera_id} is empty {now-served_date}")
                if (now-served_date).seconds > TIMEOUT:
                    running = False
                
                continue

            frame = queue.get_nowait()
            if frame is None:
                # logger.debug("frame")
                # await asyncio.sleep(0.001)
                logger.debug(f"{camera_id} got None")
                running = False
                continue
            served_date = now
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
    finally:
        # queue.task_done()
        logger.debug(f"{camera_id} is finish")
        try:
            await ss.remove_queue(camera_id, queue)
        except Exception as e:
            print(e)
            logger.exception(e)
        # logger.debug("remove queue")

    logger.debug('finish --')


@module.route("/")
async def index():
    return "Live Camera"


@module.route("/cameras/<camera_id>")
async def live(camera_id):
    ss = current_app.streaming_sub
    response = await make_response(generate_frame(camera_id, ss))
    response.timeout = None  # No timeout for this route
    response.headers["Content-Type"] = "multipart/x-mixed-replace; boundary=frame"
    return response
