from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from nokkhum import models
from mongoengine import Q
import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")
subviews = []


def index_admin(search_keyword):
    projects = models.Project.objects(
        status="active", name__icontains=search_keyword
    ).order_by("-id")
    # for project in projects:
    #     my_projects.append(project)
    return render_template("/dashboard/index.html", projects=projects)


def index_user(search_keyword):
    projects = models.Project.objects(
        Q(name__icontains=search_keyword)
        & Q(status="active")
        & (
            Q(owner=current_user._get_current_object())
            | Q(users__icontains=current_user._get_current_object())
            | Q(assistant__icontains=current_user._get_current_object())
        )
    ).order_by("-id")
    return render_template("/dashboard/index.html", projects=projects)


@module.route("/")
@login_required
def index():
    project_search = request.args.get("project_search", "")
    # print(project_search)
    # if project_search:
    #     return index_search(project_search)
    # user = current_user._get_current_object()
    if "admin" in current_user._get_current_object().roles:
        return index_admin(project_search)
    return index_user(project_search)
