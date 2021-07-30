import datetime
from flask import Blueprint, render_template, request, jsonify

from flask_login import login_required, current_user

from nokkhum import models
from mongoengine import Q


module = Blueprint("processor", __name__, url_prefix="/processor")


@module.route("/<project_id>/state", methods=["GET"])
@login_required
def get_state(project_id):
    data = []
    project = models.Project.objects.get(id=project_id)
    processors = models.Processor.objects(project=project)
    for processor in processors:
        if processor.camera.status == "Inactive":
            continue
        processor_state = {}
        processor_state["camera_id"] = str(processor.camera.id)
        processor_state["project_id"] = str(project.id)
        processor_state["state"] = processor.state
        processor_state["type"] = []

        if processor.reports and processor.state == "running":
            # del processor.reports[-1].processors["acquisitor"].
            # print(processor.reports[-1].reported_data)
            if (
                datetime.datetime.now() - processor.reports[-1].reported_data
            ).seconds >= 30:
                # continue
                processor_state["state"] = "stop"
                pass

            processor_state["type"] = [
                processor_type
                for processor_type, value in processor.reports[-1].processors.items()
                if value  # เช็คเกิน 30 วิ
            ]
            # print(processor_state)
        data.append(processor_state)
    return jsonify(data)


@module.route("/state", methods=["GET"])
@login_required
def get_state_all_projects():
    data = []
    if "admin" in current_user._get_current_object().roles:
        projects = models.Project.objects(status="active")
    else:
        projects = models.Project.objects(
            # Q(name__icontains=search_keyword)
            Q(status="active")
            & (
                Q(owner=current_user._get_current_object())
                | Q(users__icontains=current_user._get_current_object())
                | Q(assistant__icontains=current_user._get_current_object())
            )
        )
    processors = models.Processor.objects(project__in=projects)
    for processor in processors:
        if processor.camera.status == "Inactive":
            continue
        processor_state = {}
        processor_state["camera_id"] = str(processor.camera.id)
        processor_state["project_id"] = str(processor.project.id)
        processor_state["state"] = processor.state
        processor_state["type"] = []
        if processor.reports and processor.state == "running":
            # del processor.reports[-1].processors["acquisitor"]
            processor_state["type"] = [
                processor_type
                for processor_type, value in processor.reports[-1].processors.items()
                if value
            ]
        data.append(processor_state)
    return jsonify(data)


@module.route("/", methods=["GET"])
@login_required
def view():
    if "admin" in current_user._get_current_object().roles:
        projects = models.Project.objects(status="active")
    else:
        projects = models.Project.objects(
            # Q(name__icontains=search_keyword)
            Q(status="active")
            & (
                Q(owner=current_user._get_current_object())
                | Q(users__icontains=current_user._get_current_object())
                | Q(assistant__icontains=current_user._get_current_object())
            )
        )
    return render_template("/processors/processor.html", projects=projects)


@module.route("/processor_search", methods=["GET"])
@login_required
def processor_search():
    search = request.args.get("search")
    if "admin" in current_user._get_current_object().roles:
        projects = models.Project.objects(status="active")
    else:
        projects = models.Project.objects(
            Q(name__icontains=search)
            & Q(status="active")
            & (
                Q(owner=current_user._get_current_object())
                | Q(users__icontains=current_user._get_current_object())
                | Q(assistant__icontains=current_user._get_current_object())
            )
        )
    return render_template("/processors/processor.html", projects=projects)


@module.route("/resource_usage")
@login_required
def get_resource_usage():
    if "admin" in current_user._get_current_object().roles:
        projects = models.Project.objects(status="active")
    else:
        projects = models.Project.objects(
            Q(status="active")
            & (
                Q(owner=current_user._get_current_object())
                | Q(users__icontains=current_user._get_current_object())
                | Q(assistant__icontains=current_user._get_current_object())
            )
        )
    results = []
    for project in projects:
        for camera in project.cameras:
            if camera.status == "active":
                processor = models.Processor.objects.get(camera=camera)
                if processor.reports:
                    report = processor.reports[-1]
                    result = dict(
                        project=dict(id=str(project.id), name=project.name),
                        camera=dict(id=str(camera.id), name=camera.name),
                        cpu=float(
                            report.cpu
                            / report.compute_node.machine_specification.cpu_count
                        ),
                        total_memory=str(
                            report.compute_node.machine_specification.total_memory
                            // 1000000
                        ),
                        memory=str(report.memory // 1000000),
                        memory_percentage=int(
                            report.memory
                            * 100
                            / report.compute_node.machine_specification.total_memory
                        ),
                        state=str(processor.state),
                    )
                    results.append(result)
    return jsonify(results)
