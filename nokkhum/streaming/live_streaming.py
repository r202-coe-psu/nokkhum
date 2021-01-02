from quart import Blueprint, Response, g

module = Blueprint("live_streaming", __name__, url_prefix="/live")


def gen(camera_id):
    """Video streaming generator function."""
    while True:
        frame = g.cameras[camera_id].get_frame()
        if frame is None:
            break
        yield (b"--frame\r\n" b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")



@module.route("/")
async def index():
    return "asdsad"


@module.route("/cameras/<camera_id>")
async def live(camera_id):
	return Response(
        gen(camera_id), mimetype="multipart/x-mixed-replace; boundary=frame"
    )

