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
    gridviews = models.GridView.objects(user=current_user._get_current_object())
    grid_id = request.args.get("grid_id")
    num_grid = 4
    if grid_id:
        gridview = models.GridView.objects(
            user=current_user._get_current_object(), id=grid_id
        ).first()
        if gridview:
            num_grid = gridview.num_grid
    else:
        if gridviews:
            grid_id = str(gridviews[0].id)

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
        gridviews=gridviews,
        grid_id=grid_id,
        num_grid=num_grid,
    )


@module.route("/create", methods=["GET", "POST"])
@login_required
def create():
    data = request.form
    print(data)
    num_grid = data["grid"]
    name = data["name"]
    models.GridView(
        user=current_user._get_current_object(),
        name=name,
        num_grid=num_grid,
        data={"status": "initial"},
    ).save()
    return redirect(url_for("gridviews.index"))


@module.route("/save-gridviews", methods=["GET", "POST"])
@login_required
def save():
    data = request.form
    displays_data = data["displays"]
    grid_id = data["grid_id"]
    gridview = models.GridView.objects(
        user=current_user._get_current_object(), id=grid_id
    ).first()
    if not gridview:
        return Response(
            "{'status':'Not found grid template'}",
            status=404,
            mimetype="application/json",
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
    grid_id = request.args.get("grid_id")
    if "?" in grid_id:
        grid_id, _ = grid_id.split("?")
    if grid_id:
        gridview = models.GridView.objects(
            id=grid_id, user=current_user._get_current_object()
        ).first()
    else:
        gridview = models.GridView.objects(
            user=current_user._get_current_object()
        ).first()
    if gridview:
        displays_data = gridview.data

    return jsonify(displays_data)