import asyncio
from quart import (
    request,
    Blueprint,
    Response,
    g,
    make_response,
    current_app,
    stream_with_context,
    websocket,
)

import logging
import datetime

# from nokkhum.streaming import app

module = Blueprint("streaming_ws", __name__, url_prefix="/ws")
logger = logging.getLogger(__name__)


TIMEOUT = 30


async def generate_frame(camera_id, user_id, ss):
    queue = await ss.add_new_queue(camera_id, user_id)

    served_date = datetime.datetime.now()
    running = True
    try:
        logger.debug(f"{camera_id} is live")
        while running:
            now = datetime.datetime.now()
            if queue.empty():
                await asyncio.sleep(0.1)

                # logger.debug(f"{camera_id} is empty {now-served_date}")
                if (now - served_date).seconds > TIMEOUT:
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
            # await websocket.send(
            #     b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            # )
            await websocket.send(frame)
            await asyncio.sleep(0)
    finally:
        # queue.task_done()
        logger.debug(f"{camera_id} is finish")
        try:
            await ss.remove_queue(camera_id, user_id, queue)
        except Exception as e:
            logger.exception(e)


logger.debug("remove queue")


@module.websocket("")
async def index():
    logger.debug("websocket")
    await websocket.send("hello")


@module.websocket("/cameras/<camera_id>")
async def live_camera(camera_id):
    logger.debug("in web socket")
    # try:
    while True:
        # await websocket.receive()
        ss = current_app.streaming_sub
        # user_id = request.args.get("user_id")
        # data = await websocket.receive()
        await generate_frame(camera_id, None, ss)
        # await websocket.send(camera_id)
    # except asyncio.CancelledError:
    #     # Handle disconnection here
    #     await websocket.close(1000)

    # response.timeout = None  # No timeout for this route
    # response.headers["Content-Type"] = "multipart/x-mixed-replace; boundary=frame"
    # return response
