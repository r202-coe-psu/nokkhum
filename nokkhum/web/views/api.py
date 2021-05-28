import pathlib
from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    abort,
    Response,
    current_app,
)
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)
import pathlib
from nokkhum import models
from .. import forms
from .. import oauth2
import datetime
from nokkhum.web import nats


module = Blueprint("api", __name__, url_prefix="/api/v1")


@module.route("/videos/<processor_id>/<date_dir>/<filename>")
@login_required
def get_video(processor_id, date_dir, filename):
    if filename.startswith("_"):
        abort(404)

    video_path = (
        pathlib.Path(current_app.config.get("NOKKHUM_PROCESSOR_RECORDER_PATH"))
        / processor_id
        / date_dir
        / f"{filename.split('.')[0]}.mp4"
    )
    if video_path.exists():
        return Response(200)

    data = {
        "processor_id": processor_id,
        "date_dir": date_dir,
        "filename": filename,
        "action": "extract",
    }

    nats.nats_client.publish("nokkhum.storage.command", data)
    abort(404)
