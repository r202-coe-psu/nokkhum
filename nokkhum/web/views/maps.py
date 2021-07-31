from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
)
import json
from flask_login import login_required, current_user
from nokkhum import models

module = Blueprint("maps", __name__, url_prefix="/maps")


@module.route("/", methods=["GET"])
@login_required
def index():
    return "map"


@module.route("/view", methods=["GET"])
@login_required
def view():
    project_id = request.args.get("project_id")
    center = [13.736717, 100.523186]
    zoom = 12
    if project_id:
        project = models.Project.objects.get(id=project_id)
        cameras = models.Camera.objects(project=project, status="active")
        lat = 0
        lon = 0
        for camera in cameras:
            lat += camera.location[1]
            lon += camera.location[0]
        if lat and lon:
            center = [lat / cameras.count(), lon / cameras.count()]

    return render_template(
        "/map/index.html",
        zoom=zoom,
        center=center,
    )