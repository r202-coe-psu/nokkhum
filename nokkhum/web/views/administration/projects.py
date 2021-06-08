from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
)

from flask_login import current_user

from nokkhum.web import acl, forms
from nokkhum import models
import datetime
from mongoengine import Q

subviews = []

module = Blueprint(
    "projects",
    __name__,
    url_prefix="/projects",
)


@module.route("/")
@acl.admin_permission.require(http_exception=403)
def index():
    # my_projects = list()
    project_search = request.args.get("project_search", "")
    projects = models.Project.objects(
        status="active", name__icontains=project_search
    ).order_by("-id")

    if "admin" in current_user._get_current_object().roles:
        projects = models.Project.objects(
            status="active", name__icontains=project_search
        ).order_by("-id")
    else:
        projects = models.Project.objects(
            Q(name__icontains=project_search)
            & Q(status="active")
            & (
                Q(owner=current_user._get_current_object())
                | Q(users__icontains=current_user._get_current_object())
                | Q(assistant__icontains=current_user._get_current_object())
            )
        ).order_by("-id")
    # for project in projects:
    #     if (
    #         (project.is_member(current_user._get_current_object()) is True)
    #         or (project.owner == current_user._get_current_object())
    #         or ("admin" in current_user.roles)
    #     ):
    #         my_projects.append(project)
    # Q(owner=current_user._get_current_object())).order_by('-id')
    return render_template(
        "/projects/index.html", projects=projects, now=datetime.datetime.now()
    )
