from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user

from nokkhum import models
from mongoengine import Q
import datetime

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")
subviews = []


# def index_admin(search_keyword):
#     projects = models.Project.objects(
#         status="active", name__icontains=search_keyword
#     ).order_by("-id")
#     # for project in projects:
#     #     my_projects.append(project)
#     return render_template("/dashboard/index.html", projects=projects)


# def index_user(search_keyword):
#     projects = models.Project.objects(
#         Q(name__icontains=search_keyword)
#         & Q(status="active")
#         & (
#             Q(owner=current_user._get_current_object())
#             | Q(users__icontains=current_user._get_current_object())
#             | Q(assistant__icontains=current_user._get_current_object())
#         )
#     ).order_by("-id")
#     return render_template("/dashboard/index.html", projects=projects)


@module.route("/")
@login_required
def index():
    project_search = request.args.get("project_search", "")
    storage_share_list = models.StorageShare.objects(
        psu_passport_username=current_user._get_current_object().username,
        start_date__lte=datetime.date.today(),
        expire_date__gte=datetime.date.today(),
    )
    projects = models.Project.objects(
        Q(name__icontains=project_search)
        & Q(status="active")
        & (
            Q(owner=current_user._get_current_object())
            | Q(users__icontains=current_user._get_current_object())
            | Q(assistant__icontains=current_user._get_current_object())
            | Q(security_guard__icontains=current_user._get_current_object())
        )
    ).order_by("-id")

    return render_template(
        "/dashboard/index.html",
        projects=projects,
        storage_share_list=storage_share_list,
    )
