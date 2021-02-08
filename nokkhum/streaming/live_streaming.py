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

module = Blueprint("live_streaming", __name__, url_prefix="/live")
logger = logging.getLogger(__name__)


async def generate_frame(camera_id, ss):
    queue = await ss.add_new_queue(camera_id)
    # logger.debug("gen frame ")
    logger.debug(f'=>{ss.sc._loop}')
    try:
        while True:
            # logger.debug("trueee")
            if queue.empty():
                await asyncio.sleep(0.1)
                continue
            frame = queue.get_nowait()
            if frame is None:
                # logger.debug("frame")
                await asyncio.sleep(0.001)
                continue
            yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
    finally:
        try:
            logger.debug("close connection")
            queue.task_done()
            # logger.debug("finally")
            await ss.remove_queue(camera_id, queue)
            logger.debug("close connection after remove queue")
            # logger.debug("remove queue")
        except Exception as e:
            logger.debug(f"xxxx {e}")
    
    logger.debug(f"end {e}")

@module.route("/")
async def index():
    return "Live Camera"


@module.route("/cameras/<camera_id>")
async def live(camera_id):
    logger.debug("in live")
    ss = current_app.streaming_sub
    response = await make_response(generate_frame(camera_id, ss))
    response.timeout = None  # No timeout for this route
    response.headers["Content-Type"] = "multipart/x-mixed-replace; boundary=frame"
    return response
