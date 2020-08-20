from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from nokkhum import models

import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")
subviews = []


def index_admin():
    projects = models.Project.objects(status="active").order_by("-id")
    # for project in projects:
    #     my_projects.append(project)
    return render_template("/dashboard/index.html", projects=projects)


def index_user():
    my_projects = list()
    projects = models.Project.objects(status="active").order_by("-id")
    for project in projects:
        if (project.is_member(current_user._get_current_object()) is True) or (
            project.owner == current_user._get_current_object()
        ):
            my_projects.append(project)
    return render_template("/dashboard/index.html", projects=my_projects)


@module.route("/")
@login_required
def index():
    user = current_user._get_current_object()
    if "admin" in user.roles:
        return index_admin()
    return index_user()
