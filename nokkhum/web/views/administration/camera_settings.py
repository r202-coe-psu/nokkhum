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
    "camera_settings",
    __name__,
    url_prefix="/camera_settings",
)


@module.route("/brands")
@acl.admin_permission.require(http_exception=403)
def brands_index():
    # for project in projects:
    #     if (
    #         (project.is_member(current_user._get_current_object()) is True)
    #         or (project.owner == current_user._get_current_object())
    #         or ("admin" in current_user.roles)
    #     ):
    #         my_projects.append(project)
    # Q(owner=current_user._get_current_object())).order_by('-id')
    camera_brands = models.CameraBrand.objects()
    return render_template(
        "/cameras/brands_list.html",
        camera_brands=camera_brands,
    )


@module.route("/brands/create", methods=["GET", "POST"])
@acl.admin_permission.require(http_exception=403)
def create_brand():
    data = request.form
    name = data["name"]
    camera_brand = models.CameraBrand.objects(name=name).first()
    if not camera_brand:
        models.CameraBrand(name=name).save()
    return redirect(url_for("administration.camera_settings.brands_index"))


@module.route("/brands/<brand_id>/delete", methods=["GET", "POST"])
@acl.admin_permission.require(http_exception=403)
def delete_brand(brand_id):
    camera_brand = models.CameraBrand.objects(id=brand_id).delete()
    return redirect(url_for("administration.camera_settings.brands_index"))
