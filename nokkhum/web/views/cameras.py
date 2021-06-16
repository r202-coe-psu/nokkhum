from nokkhum.models import projects
from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    url_for,
    Response,
    g,
    current_app,
)
import datetime
from flask_login import login_required, current_user
import json
from nokkhum import models
from nokkhum.web import nats

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
        ("640*360", "640 x 360"),
        ("640*480", "640 x 480"),
        ("854*480", "854 x 480"),
        ("1280*720", "1280 x 720"),
        ("1920*1080", "1920 x 1080"),
    ]
    if not form.validate_on_submit():
        return render_template(
            "/cameras/add-edit-camera.html", form=form, project=project
        )
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
    camera = models.Camera.objects(id=camera_id).first()
    if camera is None:
        return render_template("/projects/project.html")
    processor = camera.get_processor()
    date_dirs = get_dir_by_processor(str(processor.id))
    # print(date_dirs)
    files_list = []
    videos_path = []
    date_dir = datetime.datetime.now().strftime("%Y%m%d")
    # if date_dirs:
    files_list = get_file_by_dir_date(str(processor.id), date_dir)
    if files_list:
        files_list.sort(reverse=True)
        files_list = files_list[:5]

    for file in files_list:
        videos_path.append(
            get_video_path(str(processor.id), date_dirs[0].name, file.name)
        )
    # print(videos_path)
    return render_template(
        "/cameras/camera.html",
        camera=camera,
        processor=processor,
        project=project,
        date_dir=date_dir,
        files_list=files_list,
        videos_path=videos_path,
    )


@module.route("/view-advance", methods=["GET"])
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
    if not camera.motion_property:
        motion_property = models.MotionProperty()
        camera.update(motion_property=motion_property)
    if not project.is_assistant_or_owner(current_user._get_current_object()):
        return redirect(url_for("projects.view", project_id=project_id))
    if not form.validate_on_submit():
        form.frame_size.data = f"{camera.width}*{camera.height}"
        form.longitude.data = camera.location[0]
        form.latitude.data = camera.location[1]
        form.storage_period.data = processor.storage_period
        form.motion_detector.data = camera.motion_property.active
        form.sensitivity.data = camera.motion_property.sensitivity
        return render_template(
            "/cameras/add-edit-camera.html", form=form, camera=camera, project=project
        )

    width, height = form.frame_size.data.split("*")
    processor.storage_period = form.storage_period.data
    processor.save()
    camera.location = [form.longitude.data, form.latitude.data]
    form.populate_obj(camera)
    camera.width = width
    camera.height = height
    camera.motion_property.active = form.motion_detector.data
    camera.motion_property.sensitivity = form.sensitivity.data
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

    nats.nats_client.publish("nokkhum.processor.command", data)

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
    nats.nats_client.publish("nokkhum.processor.command", data)
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
