from flask import Blueprint, render_template, redirect, request, url_for, Response, g

from flask_login import login_required, current_user
import json
from nokkhum import models

from .. import forms
from .storages import get_storage_path

module = Blueprint("cameras", __name__, url_prefix="/cameras")


@module.route("/add", methods=["GET", "POST"])
@login_required
def add():
    project_id = request.args.get("project_id")
    form = forms.cameras.CameraForm()
    form.frame_size.choices = [
        ("640*360", "640 x 360"),
        ("854*480", "854 x 480"),
        ("1280*720", "1280 x 720"),
        ("1920*1080", "1920 x 1080"),
    ]
    project = models.Project.objects.get(id=project_id)
    if not (
        "admin" in current_user.roles
        or current_user == project.owner
        or current_user in project.assistant
    ):
        return redirect(url_for("projects.view", project_id=project_id))
    if not form.validate_on_submit():
        return render_template("/cameras/add-camera.html", form=form, project=project)
    width, height = form.frame_size.data.split("*")
    camera = models.Camera(
        name=form.name.data,
        frame_rate=form.frame_rate.data,
        width=width,
        height=height,
        location=[form.longitude.data, form.latitude.data],
        uri=form.uri.data,
        project=project,
    )
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
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    processor = camera.get_processor()
    root = get_storage_path()
    processor_path = root / str(processor.id)
    date_dirs = [p for p in processor_path.iterdir() if p.is_dir()]
    print(date_dirs[-1])

    # processor_path = root / str(processor.id) / date_dirs[-1].name

    if camera is None:
        return render_template("/projects/project.html")
    return render_template(
        "/cameras/camera.html",
        camera=camera,
        project=project,
        date_dir=date_dirs[-1],
    )


@module.route("/view_advance", methods=["GET"])
@login_required
def view_advance():
    project_id = request.args.get("project_id")
    camera_id = request.args.get("camera_id")
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    if camera is None:
        return render_template("/projects/project.html")
    return render_template(
        "/cameras/camera-advance.html", camera=camera, project=project
    )


@module.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    project_id = request.args.get("project_id")
    camera_id = request.args.get("camera_id")
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    processor = models.Processor.objects.get(camera=camera, project=project)
    form = forms.cameras.CameraForm(obj=camera)
    form.frame_size.choices = [
        ("640*360", "640 x 360"),
        ("854*480", "854 x 480"),
        ("1280*720", "1280 x 720"),
        ("1920*1080", "1920 x 1080"),
    ]
    if not (
        "admin" in current_user.roles
        or current_user == project.owner
        or current_user in project.assistant
    ):
        return redirect(url_for("projects.view", project_id=project_id))
    if not form.validate_on_submit():
        form.frame_size.data = f"{camera.width}*{camera.height}"
        form.longitude.data = camera.location[0]
        form.latitude.data = camera.location[1]
        form.storage_period.data = processor.storage_period
        return render_template(
            "/cameras/add-camera.html", form=form, camera=camera, project=project
        )
    width, height = form.frame_size.data.split("*")
    processor.storage_period = form.storage_period.data
    processor.save()
    camera.location = [form.longitude.data, form.latitude.data]
    form.populate_obj(camera)
    camera.width = width
    camera.height = height
    camera.save()
    return redirect(url_for("projects.view", project_id=project.id))


@module.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    project_id = request.args.get("project_id")
    camera_id = request.args.get("camera_id")
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    if "admin" in current_user.roles or current_user == project.owner:
        camera.status = "Inactive"
        camera.save()
    return redirect(url_for("projects.view", project_id=project.id))


@module.route("/grid-view", methods=["GET"])
@login_required
def grid_view():
    project_id = request.args.get("project_id")
    camera_list = []
    project = models.Project.objects.get(id=project_id)
    camera_id_list = request.args.get("cameras").split(",")
    for camera_id in camera_id_list:
        camera = models.Camera.objects.get(id=camera_id)
        camera_list.append(camera)
    return render_template(
        "/cameras/camera-selected.html", project=project, camera_list=camera_list
    )


@module.route("/<camera_id>/startlpr", methods=["POST"])
@login_required
def start_lpr_process(camera_id):
    # print(request.form.get('camera_id'))
    # print(current_user._get_current_object().id)
    project_id = request.form.get("project_id")
    data = json.dumps(
        {
            "action": "start",
            "camera_id": camera_id,
            "project_id": project_id,
            "user_id": str(current_user._get_current_object().id),
        }
    )
    loop = g.get_loop()
    nats_client = g.get_nats_client()
    loop.run_until_complete(
        nats_client.publish("nokkhum.processor.command", data.encode())
    )
    response = Response()
    response.status_code = 200
    return response


@module.route("/<camera_id>/stoplpr", methods=["GET", "POST"])
@login_required
def stop_lpr_process(camera_id):
    # print(request.form.get('camera_id'))
    project_id = request.form.get("project_id")
    data = json.dumps(
        {
            "action": "stop",
            "camera_id": camera_id,
            "project_id": project_id,
            "user_id": str(current_user._get_current_object().id),
        }
    )

    loop = g.get_loop()
    nats_client = g.get_nats_client()
    loop.run_until_complete(
        nats_client.publish("nokkhum.processor.command", data.encode())
    )
    response = Response()
    response.status_code = 200
    return response


# @module.route('/init_camera', methods=['GET', 'POST'])
# @login_required
# def init_camera():
#     project_id = request.args.get('project_id')
#     project = models.Project.objects.get(id=project_id)
#     form = forms.cameras.InitCameraForm()
#     if 'admin' in current_user.roles or current_user == project.owner or current_user in project.assistant:
#         if not form.validate_on_submit():
#             return render_template('/cameras/init-camera.html',
#                                    form=form,
#                                    project=project)

#         format_parameter_list = []
#         if '<username>' in form.rtsp_url.data:
#             format_parameter_list.append('username')
#         if '<password>' in form.rtsp_url.data:
#             format_parameter_list.append('password')
#         if '<ip_address>' in form.rtsp_url.data:
#             format_parameter_list.append('ip_address')
#         if '<port>' in form.rtsp_url.data:
#             format_parameter_list.append('port')

#         carmera_model = models.CameraModel(name=form.model_name.data,
#                                            format_parameter=format_parameter_list,
#                                            rtsp_url=form.rtsp_url.data)
#         camera_brand = models.CameraBrand(name=form.brand_name.data,
#                                           camera_models=carmera_model)
#         camera_brand.save()


#     else:
#         if not form.validate_on_submit():
#             return render_template('/cameras/init-camera.html',
#                                    form=form,
#                                    project=project)
#     return redirect(url_for('cameras.add'))
