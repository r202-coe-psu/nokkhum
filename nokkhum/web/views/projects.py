from nokkhum.models.cameras import Camera
from flask import Blueprint, render_template, redirect, url_for, request, jsonify

from flask_login import login_required, current_user

from nokkhum import models

from .. import forms

# import asyncio
import datetime
from mongoengine import Q


module = Blueprint("projects", __name__, url_prefix="/projects")


@module.route("/")
@login_required
def index():
    # my_projects = list()
    project_search = request.args.get("project_search", "")
    projects = models.Project.objects(
        Q(name__icontains=project_search)
        & Q(status="active")
        & (
            Q(owner=current_user._get_current_object())
            | Q(users__icontains=current_user._get_current_object())
            | Q(assistant__icontains=current_user._get_current_object())
        )
    ).order_by("-id")

    return render_template(
        "/projects/index.html", projects=projects, now=datetime.datetime.now()
    )


@module.route("/create", methods=["GET", "POST"])
@login_required
def create():
    project_name = request.form.get("name")
    # print(project_name)
    if not project_name:
        return redirect(request.referrer)
    project = models.Project.objects(name=project_name).first()
    if project:
        return redirect(request.referrer)
    project = models.Project(
        name=project_name, owner=current_user._get_current_object()
    )
    project.users.append(current_user._get_current_object())
    project.created_date = datetime.datetime.now()
    project.updated_date = datetime.datetime.now()
    project.save()
    return redirect(request.referrer)


@module.route("/<project_id>/edit", methods=["GET", "POST"])
@login_required
def edit(project_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_assistant_or_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    form = forms.projects.ProjectForm(obj=project)
    if not form.validate_on_submit():
        return render_template(
            "/projects/edit-project.html", form=form, project=project
        )
    form.populate_obj(project)
    project.save()
    return redirect(url_for("projects.index"))


@module.route("/<project_id>/view", methods=["GET"])
@login_required
def view(project_id):
    project = None
    project = models.Project.objects.get(id=project_id)
    if not project.is_member(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))

    processors = models.Processor.objects(project=project)
    return render_template(
        "/projects/project.html", project=project, processors=processors
    )


@module.route("/<project_id>/delete", methods=["GET", "POST"])
@login_required
def delete(project_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    for camera in project.cameras:
        camera.status = "Inactive"
        camera.save()
    project.status = "Inactive"
    project.save()
    return redirect(url_for("projects.index"))


@module.route("/<project_id>/add_contributor_page")
@login_required
def add_contributor_page(project_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_assistant_or_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    users = models.User.objects()
    # if project.is_member(current_user._get_current_object()) is False:
    #     return redirect(url_for("dashboard.index"))
    return render_template(
        "/projects/add-contributor.html", project=project, users=users
    )


@module.route("/<project_id>/add_contributor", methods=["GET"])
@login_required
def add_contributor(project_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_assistant_or_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    added_user_id = request.args.get("add-user")
    if added_user_id:
        added_user = models.User.objects.get(id=added_user_id)
        if added_user not in project.users:
            project.users.append(added_user)
            project.save()
    return redirect(url_for("projects.add_contributor_page", project_id=project_id))


@module.route("/<project_id>/delete_contributor/<user_id>", methods=["GET"])
@login_required
def delete_contributor(project_id, user_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    delete_user = models.User.objects.get(id=user_id)
    if delete_user in project.users:
        project.users.remove(delete_user)
    if delete_user in project.assistant:
        project.assistant.remove(delete_user)
    if delete_user in project.security_guard:
        project.security_guard.remove(delete_user)
    project.save()
    return redirect(url_for("projects.add_contributor_page", project_id=project_id))


@module.route("/<project_id>/add_assistant/<user_id>", methods=["GET"])
@login_required
def add_assistant(project_id, user_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    assistant = models.User.objects.get(id=user_id)
    if assistant not in project.users:
        return redirect(url_for("projects.add_contributor_page", project_id=project_id))

    if assistant not in project.assistant:
        project.assistant.append(assistant)
        project.save()
    return redirect(url_for("projects.add_contributor_page", project_id=project_id))


@module.route("/<project_id>/demote_assistant/<user_id>", methods=["GET"])
@login_required
def demote_assistant(project_id, user_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    assistant = models.User.objects.get(id=user_id)
    if assistant in project.assistant:
        project.assistant.remove(assistant)
        project.save()
    return redirect(url_for("projects.add_contributor_page", project_id=project_id))


@module.route("/<project_id>/add_security_guard/<user_id>", methods=["GET"])
@login_required
def add_security_guard(project_id, user_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    security_guard = models.User.objects.get(id=user_id)
    if security_guard not in project.users:
        return redirect(url_for("projects.add_contributor_page", project_id=project_id))

    if security_guard not in project.security_guard:
        project.security_guard.append(security_guard)
        project.save()
    return redirect(url_for("projects.add_contributor_page", project_id=project_id))


@module.route("/<project_id>/demote_security_guard/<user_id>", methods=["GET"])
@login_required
def demote_security_guard(project_id, user_id):
    project = models.Project.objects.get(id=project_id)
    if not project.is_owner(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    security_guard = models.User.objects.get(id=user_id)
    if security_guard in project.security_guard:
        project.security_guard.remove(security_guard)
        project.save()
    return redirect(url_for("projects.add_contributor_page", project_id=project_id))


@module.route("/<project_id>/get_camera_location")
@login_required
def get_camera_location_in_project(project_id):
    project = models.Project.objects.get(id=project_id)
    cameras = models.Camera.objects(project=project, status="active")
    result = []
    for camera in cameras:
        data = {
            "name": camera.name,
            "location": camera.location,
            "camera_id": str(camera.id),
        }
        result.append(data)
    return jsonify(result)
