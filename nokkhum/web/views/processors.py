from flask import (Blueprint,
                   render_template,
                   request,
                   jsonify)

from flask_login import login_required, current_user

from nokkhum import models
from mongoengine import Q


module = Blueprint('processor', __name__, url_prefix='/processor')


@module.route('/<project_id>/state', methods=['GET'])
@login_required
def get_state(project_id):
    data = []
    project = models.Project.objects.get(id=project_id)
    processors = models.Processor.objects(project=project)
    for processor in processors:
        if processor.camera.status == 'Inactive':
            continue
        processor_state = {}
        processor_state['camera_id'] = str(processor.camera.id)
        processor_state['project_id'] = str(project.id)
        processor_state['state'] = processor.state
        data.append(processor_state)
    return jsonify(data)


@module.route('/', methods=['GET'])
@login_required
def view():
    if 'admin' in current_user.roles:
        projects = models.Project.objects()
    else:
        projects = models.Project.objects(
            owner=current_user._get_current_object()).order_by('+id')
    return render_template('/processors/processor.html',

                           projects=projects
                           )


@module.route('/processor_search', methods=["GET"])
@login_required
def processor_search():
    search = request.args.get('search')
    if 'admin' in current_user.roles:
        projects = models.Project.objects(Q(name__icontains=search))
    else:
        projects = models.Project.objects(Q(name__icontains=search) &
                                        Q(owner=current_user._get_current_object()))
    return render_template('/processors/processor.html',
                           projects=projects)


@module.route('/resource_usage')
@login_required
def get_resource_usage():
    if 'admin' in current_user.roles:
        projects = models.Project.objects()
    else:
        projects = models.Project.objects(
            owner=current_user._get_current_object()).order_by('+id')
    results = []
    for project in projects:
        for camera in project.cameras:
            if camera.status == 'active':
                resource = models.Processor.objects.get(camera=camera)
                if  resource.report:
                    report = resource.report[-1]
                    result = dict(
                        project=dict(
                            id=str(project.id),
                            name=project.name
                        ),
                        camera=dict(
                            id=str(camera.id),
                            name=camera.name
                        ),
                        cpu=str(report.cpu/report.compute_node.machine_specification.cpu_count),
                        memory=str(report.memory//1000000),
                        state=str(resource.state)
                    )
                    results.append(result)
    return jsonify(results)
