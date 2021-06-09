from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
    Response,
    jsonify,
)

from flask_login import login_required, current_user
import json
from nokkhum import models
from mongoengine import Q
from .. import forms
from .storages import get_dir_by_processor, get_file_by_dir_date, get_video_path

module = Blueprint("gridviews", __name__, url_prefix="/gridviews")


@module.route("/", methods=["GET"])
@login_required
def index():
    num_grids = [4, 10, 13, 16, 32]
    # user = models.User.objects.get(id=current_user._get_current_object().id)
    gridviews_name = models.GridView.objects(
        user=current_user._get_current_object()
    ).values_list("name")
    projects = models.Project.objects(
        # Q(name__icontains=project_search)
        Q(status="active")
        & (
            Q(owner=current_user._get_current_object())
            | Q(users__icontains=current_user._get_current_object())
            | Q(assistant__icontains=current_user._get_current_object())
            | Q(security_guard__icontains=current_user._get_current_object())
        )
    )

    return render_template(
        "/cameras/gridview.html",
        projects=projects,
        num_grids=num_grids,
        gridviews_name=gridviews_name,
    )


@module.route("/save-gridviews", methods=["GET", "POST"])
@login_required
def save():
    data = request.form
    displays_data = data["displays"]
    num_grids = data["num_grids"]
    gridview = models.GridView.objects(
        user=current_user._get_current_object(), type=f"grid-{num_grids}"
    ).first()
    if not gridview:
        gridview = models.GridView(
            user=current_user._get_current_object(), type=f"grid-{num_grids}"
        )
    # print("1", displays_data)
    displays_data = json.loads(displays_data)
    # print("2", displays_data)
    gridview.data = displays_data
    gridview.save()
    return Response("{'status':'ok'}", status=200, mimetype="application/json")


@module.route("/get-gridviews", methods=["GET"])
@login_required
def get_grid():
    # data = request.form
    displays_data = {}
    num_grids = request.args.get("grid", 4)
    if "?" in num_grids:
        num_grids, _ = num_grids.split("?")

    gridview = models.GridView.objects(
        user=current_user._get_current_object(), type=f"grid-{num_grids}"
    ).first()
    if gridview:
        displays_data = gridview.data

    return jsonify(displays_data)