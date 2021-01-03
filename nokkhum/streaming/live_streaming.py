import asyncio
from quart import Blueprint, Response, g, make_response, current_app

module = Blueprint("live_streaming", __name__, url_prefix="/live")


async def generate_frame(queue):
    """Video streaming generator function."""
    while True:
        frame = await queue.get()
        if frame is None:
            break

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")



@module.route("/")
async def index():
    return "asdsad"


@module.route("/cameras/<camera_id>")
async def live(camera_id):

    queue = None
    while not queue:
        g = current_app
        queue = g.queues.get(camera_id)
        if not queue:
            await asyncio.sleep(0.001)
            continue
    
    return Response(
            generate_frame(queue),
            200,
            {
                'Content-Type': "multipart/x-mixed-replace; boundary=frame",
                'mimetype': "multipart/x-mixed-replace; boundary=frame",
            }
            )
