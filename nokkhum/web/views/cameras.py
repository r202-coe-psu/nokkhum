from flask import (Blueprint,
                   render_template,
                   redirect,
                   request,
                   url_for,
                   Response,
                   g)

from flask_login import login_required, current_user
import json
from nokkhum import models

from .. import forms


module = Blueprint('cameras', __name__, url_prefix='/cameras')


@module.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    project_id = request.args.get('project_id')
    form = forms.cameras.CameraForm()
    project = models.Project.objects.get(id=project_id)
    if 'admin' in current_user.roles or current_user == project.owner or current_user in project.assistant:
        if not form.validate_on_submit():
            return render_template('/cameras/add-camera.html',
                                   form=form,
                                   project=project)
        camera = models.Camera(name=form.name.data,
                               frame_rate=form.frame_rate.data,
                               width=form.width.data,
                               height=form.height.data,
                               location=[form.longitude.data, form.latitude.data],
                               uri=form.uri.data)
        camera.save()
        project.cameras.append(camera)
        project.save()
        processor = models.Processor(camera=camera,
                                     project=project,
                                     storage_period=form.storage_period.data)
        processor.save()
    else:
        if not form.validate_on_submit():
            return render_template('/cameras/add-camera.html',
                                   form=form,
                                   project=project)
    return redirect(url_for('projects.view', project_id=project.id))


@module.route('/view', methods=['GET'])
@login_required
def view():
    project_id = request.args.get('project_id')
    camera_id = request.args.get('camera_id')
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    if camera is None:
        return render_template('/projects/project.html')
    return render_template('/cameras/camera.html',
                           camera=camera, project=project)


@module.route('/view_advance', methods=['GET'])
@login_required
def view_advance():
    project_id = request.args.get('project_id')
    camera_id = request.args.get('camera_id')
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    if camera is None:
        return render_template('/projects/project.html')
    return render_template('/cameras/camera-advance.html',
                           camera=camera, project=project)


@module.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    project_id = request.args.get('project_id')
    camera_id = request.args.get('camera_id')
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    processor = models.Processor.objects.get(camera=camera,
                                             project=project)
    form = forms.cameras.CameraForm(obj=camera)
    if 'admin' in current_user.roles or current_user == project.owner or current_user in project.assistant:
        if not form.validate_on_submit():
            form.longitude.data = camera.location[0]
            form.latitude.data = camera.location[1]
            form.storage_period.data = processor.storage_period
            return render_template('/cameras/edit-camera.html',
                                   form=form,
                                   camera=camera,
                                   project=project)
        processor.storage_period = form.storage_period.data
        processor.save()
        camera.location = [form.longitude.data, form.latitude.data]
        form.populate_obj(camera)
        camera.save()
    else:
        if not form.validate_on_submit():
            form.longitude.data = camera.location[0]
            form.latitude.data = camera.location[1]
            form.storage_period.data = processor.storage_period
            return render_template('/cameras/edit-camera.html',
                                   form=form,
                                   camera=camera,
                                   project=project)

    return redirect(url_for('projects.view', project_id=project.id))


@module.route('/delete', methods=['GET', 'POST'])
@login_required
def delete():
    project_id = request.args.get('project_id')
    camera_id = request.args.get('camera_id')
    project = models.Project.objects.get(id=project_id)
    camera = models.Camera.objects.get(id=camera_id)
    if 'admin' in current_user.roles or current_user == project.owner:
        camera.status = 'Inactive'
        camera.save()
    return redirect(url_for('projects.view', project_id=project.id))


@module.route('/grid-view', methods=['GET'])
@login_required
def grid_view():
    project_id = request.args.get('project_id')
    camera_list = []
    project = models.Project.objects.get(id=project_id)
    camera_id_list = request.args.get('cameras').split(',')
    for camera_id in camera_id_list:
        camera = models.Camera.objects.get(id=camera_id)
        camera_list.append(camera)
    return render_template('/cameras/camera-selected.html',
                           project=project,
                           camera_list=camera_list)


@module.route('/<camera_id>/startlpr', methods=['POST'])
@login_required
def start_lpr_process(camera_id):
    # print(request.form.get('camera_id'))
    # print(current_user._get_current_object().id)
    project_id = request.form.get('project_id')
    data = json.dumps(
                {'action': 'start',
                 'camera_id': camera_id,
                 'project_id': project_id,
                 'user_id': str(current_user._get_current_object().id)
                 }
                )
    loop = g.get_loop()
    nats_client = g.get_nats_client()
    loop.run_until_complete(nats_client.publish(
        'nokkhum.processor.command',
        data.encode()
        ))
    response = Response()
    response.status_code = 200
    return response


@module.route('/<camera_id>/stoplpr', methods=['GET', 'POST'])
@login_required
def stop_lpr_process(camera_id):
    # print(request.form.get('camera_id'))
    project_id = request.form.get('project_id')
    data = json.dumps(
                {'action': 'stop',
                 'camera_id': camera_id,
                 'project_id': project_id,
                 'user_id': str(current_user._get_current_object().id)
                 }
                )

    loop = g.get_loop()
    nats_client = g.get_nats_client()
    loop.run_until_complete(nats_client.publish(
        'nokkhum.processor.command',
        data.encode()
        ))
    response = Response()
    response.status_code = 200
    return response
