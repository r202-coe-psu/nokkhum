from nokkhum.models import cameras, projects
from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
    Response,
    g,
    current_app,
    jsonify,
)
import datetime
from flask_login import login_required, current_user
import json
from nokkhum import models
from nokkhum.web.client import nats_client

from .. import forms
from .storages import get_dir_by_processor, get_file_by_dir_date, get_video_path

module = Blueprint("cameras", __name__, url_prefix="/cameras")


@module.route("/add", methods=["GET", "POST"])
@login_required
def add():
    project_id = request.args.get("project_id")
    project = models.Project.objects.get(id=project_id)
    if not project.is_assistant_or_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    form = forms.cameras.CameraForm()
    form.frame_size.choices = [
        ("352*288", "352 x 288"),
        ("480*240", "480 x 240"),
        ("640*360", "640 x 360"),
        ("640*480", "640 x 480"),
        ("704*576", "704 x 576"),
        ("854*480", "854 x 480"),
        ("1280*720", "1280 x 720"),
        ("1920*1080", "1920 x 1080"),
    ]
    brands = models.CameraBrand.objects().order_by("name")
    choices = [("", "Select Brand")] + [(str(brand.id), brand.name) for brand in brands]
    # print(choices)
    form.brand.choices = choices
    # form.model.choices = [("", "-")]
    model_id = request.form.get("model_id")

    if not form.validate_on_submit():
        print(form.errors)
        return render_template(
            "/cameras/add-edit-camera.html", form=form, project=project
        )
    # uri = form.protocal.data
    # if "[USERNAME]" in form.path.data:
    # print(form.model.data)
    camera_model = None
    if model_id:
        camera_model = models.CameraModel.objects.get(id=model_id)
    # path = ""
    width, height = form.frame_size.data.split("*")
    motion_property = models.MotionProperty()
    camera = models.Camera(
        name=form.name.data,
        frame_rate=form.frame_rate.data,
        width=width,
        height=height,
        location=[form.longitude.data, form.latitude.data],
        uri=form.uri.data,
        project=project,
        motion_property=motion_property,
    )
    if form.ip_address.data and camera_model:
        # if "[USERNAME]" in camera_model.path or "[PASSWORD]" in camera_model.path:
        path = (camera_model.path.replace("[USERNAME]", form.username.data)).replace(
            "[PASSWORD]", form.password.data
        )
        # uri = f"{camera_model.protocal}{form.ip_address.data}{camera_model.port}{path}"
        # else:
        if camera_model.port:
            address = f"{form.ip_address.data}:{camera_model.port}"
        else:
            address = form.ip_address.data
        uri = f"{camera_model.protocal}{form.username.data}:{form.password.data}@{address}{path}"
        uri = uri.replace("[CHANNEL]", str(form.channel.data))
        camera.uri = uri
        camera.ip_address = form.ip_address.data
        camera.username = form.username.data
        camera.password = form.password.data
        camera.channel = form.channel.data
        camera.model_id = model_id

    camera.motion_property.active = form.motion_detector.data
    camera.motion_property.sensitivity = form.sensitivity.data
    camera.save()
    processor = models.Processor(
        camera=camera, project=project, storage_period=form.storage_period.data
    )
    processor.save()

    return redirect(url_for("projects.view", project_id=project.id))


@module.route("/view", methods=["GET"])
@login_required
def view():
    project_id = request.args.get("project_id")
    camera_id = request.args.get("camera_id")
    project = models.Project.objects(id=project_id).first()
    if not project.is_member(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    if "?" in camera_id:
        camera_id = camera_id.split("?")[0]
    camera = models.Camera.objects(id=camera_id).first()
    if camera is None:
        return render_template("/projects/project.html")
    processor = camera.get_processor()
    # date_dirs = get_dir_by_processor(str(processor.id))
    # print(date_dirs)
    file_dict = {}
    date_dir = datetime.datetime.now().strftime("%Y%m%d")
    file_by_date = get_file_by_dir_date(str(processor.id), date_dir)
    # files_dict
    for file in sorted(file_by_date.keys(), reverse=True)[:5]:
        file_dict[file] = file_by_date[file]
    return render_template(
        "/cameras/camera.html",
        camera=camera,
        processor=processor,
        project=project,
        date_dir=date_dir,
        file_dict=file_dict,
        # videos_path=videos_path,
    )


# @module.route("/view-advance", methods=["GET"])
# @login_required
# def view_advance():
#     project_id = request.args.get("project_id")
#     camera_id = request.args.get("camera_id")
#     project = models.Project.objects.get(id=project_id)
#     camera = models.Camera.objects.get(id=camera_id)
#     if camera is None:
#         return render_template("/projects/project.html")
#     return render_template(
#         "/cameras/camera-advance.html", camera=camera, project=project
#     )


@module.route("/<camera_id>/edit", methods=["GET", "POST"])
@login_required
def edit(camera_id):
    project_id = request.args.get("project_id")
    # camera_id = request.args.get("camera_id")
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    processor = models.Processor.objects.get(camera=camera, project=project)
    form = forms.cameras.CameraForm(obj=camera)
    form.frame_size.choices = [
        ("352*288", "352 x 288"),
        ("480*240", "480 x 240"),
        ("640*360", "640 x 360"),
        ("640*480", "640 x 480"),
        ("704*576", "704 x 576"),
        ("854*480", "854 x 480"),
        ("1280*720", "1280 x 720"),
        ("1920*1080", "1920 x 1080"),
    ]

    if not camera.motion_property:
        motion_property = models.MotionProperty()
        camera.update(motion_property=motion_property)
    if not project.is_assistant_or_owner(current_user._get_current_object()):
        return redirect(url_for("projects.view", project_id=project_id))
    brands = models.CameraBrand.objects().order_by("name")
    choices = [("", "Select Brand")] + [(str(brand.id), brand.name) for brand in brands]
    form.brand.choices = choices

    if not form.validate_on_submit():
        # print(type(form.frame_rate.data))
        form.frame_size.data = f"{camera.width}*{camera.height}"
        form.longitude.data = camera.location[0]
        form.latitude.data = camera.location[1]
        form.storage_period.data = processor.storage_period
        form.motion_detector.data = camera.motion_property.active
        form.sensitivity.data = camera.motion_property.sensitivity
        if camera.model_id:
            camera_model = models.CameraModel.objects.get(id=camera.model_id)
            form.brand.data = str(camera_model.brand.id)
        return render_template(
            "/cameras/add-edit-camera.html", form=form, camera=camera, project=project
        )
    form.populate_obj(camera)
    model_id = request.form.get("model_id")
    camera_model = None
    if model_id:
        camera_model = models.CameraModel.objects.get(id=model_id)
    if form.ip_address.data and camera_model:
        # if "[USERNAME]" in camera_model.path or "[PASSWORD]" in camera_model.path:
        path = (camera_model.path.replace("[USERNAME]", form.username.data)).replace(
            "[PASSWORD]", form.password.data
        )
        #     uri = f"{camera_model.protocal}{form.ip_address.data}{camera_model.port}{path}"
        # else:
        if camera_model.port:
            address = f"{form.ip_address.data}:{camera_model.port}"
        else:
            address = form.ip_address.data
        uri = f"{camera_model.protocal}{form.username.data}:{form.password.data}@{address}{path}"
        uri = uri.replace("[CHANNEL]", str(form.channel.data))
        camera.uri = uri
        camera.model_id = model_id

    width, height = form.frame_size.data.split("*")
    processor.storage_period = form.storage_period.data
    processor.save()
    camera.location = [form.longitude.data, form.latitude.data]
    camera.width = width
    camera.height = height
    camera.motion_property.active = form.motion_detector.data
    camera.motion_property.sensitivity = form.sensitivity.data
    camera.model_id = model_id
    camera.save()
    return redirect(url_for("projects.view", project_id=project.id))


@module.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    project_id = request.args.get("project_id")
    camera_id = request.args.get("camera_id")
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    if not project.is_owner(current_user._get_current_object()):
        return redirect(url_for("projects.view", project_id=project_id))
    camera.status = "Inactive"
    camera.save()
    return redirect(url_for("projects.view", project_id=project.id))


@module.route("/<camera_id>/start-recorder", methods=["POST"])
@login_required
def start_recorder(camera_id):
    project_id = request.form.get("project_id")
    project = models.Project.objects.get(id=project_id)
    if not project.is_assistant_or_owner(current_user._get_current_object()):
        return Response(403)

    camera = models.Camera.objects.get(id=camera_id)
    data = {
        "action": "start-recorder",
        "camera_id": camera_id,
        "project_id": project_id,
        "user_id": str(current_user._get_current_object().id),
    }

    if camera.motion_property.active:
        data["motion"] = camera.motion_property.active
        data["sensitivity"] = camera.motion_property.sensitivity

    nats_client.nats_client.publish("nokkhum.processor.command", data)

    response = Response()
    response.status_code = 200
    return response


@module.route("/<camera_id>/stop-recorder", methods=["GET", "POST"])
@login_required
def stop_recorder(camera_id):
    # print(request.form.get('camera_id'))
    project_id = request.form.get("project_id")
    project = models.Project.objects.get(id=project_id)
    if not project.is_assistant_or_owner(current_user._get_current_object()):
        return Response(403)
    data = {
        "action": "stop-recorder",
        "camera_id": camera_id,
        "project_id": project_id,
        "user_id": str(current_user._get_current_object().id),
    }
    nats_client.nats_client.publish("nokkhum.processor.command", data)
    response = Response()
    response.status_code = 200
    return response


@module.route("/brands/<brand_id>/get_models", methods=["GET"])
@login_required
def get_models_by_brand(brand_id):
    brand = models.CameraBrand.objects.get(id=brand_id)
    camera_models = models.CameraModel.objects(brand=brand).order_by("name")
    choices = [(str(model.id), model.name) for model in camera_models]
    return jsonify(choices)


@module.route("/<camera_id>/initial_form", methods=["GET"])
@login_required
def initial_form(camera_id):
    camera = models.Camera.objects.get(id=camera_id)
    data = {"type": "uri"}
    if camera.model_id:
        camera_model = models.CameraModel.objects.get(id=camera.model_id)
        camera_models = models.CameraModel.objects(brand=camera_model.brand).order_by(
            "name"
        )
        data["model_id"] = camera.model_id
        choices = [(str(model.id), model.name) for model in camera_models]
        data["choices"] = choices
        data["type"] = "model"
    return jsonify(data)
