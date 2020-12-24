from quart import Blueprint

module = Blueprint("live_streaming", __name__, url_prefix="/live")


@module.route("/")
async def index():
    return "asdsad"
