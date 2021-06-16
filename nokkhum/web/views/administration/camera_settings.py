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


@module.route("/brands/<brand_id>/edit", methods=["GET", "POST"])
@acl.admin_permission.require(http_exception=403)
def edit_brand(brand_id):
    camera_brand = models.CameraBrand.objects.get(id=brand_id)
    form = forms.cameras.CameraBrandForm(obj=camera_brand)
    if not form.validate_on_submit():
        return render_template(
            "/cameras/brand_edit.html", form=form, camera_brand=camera_brand
        )
    form.populate_obj(camera_brand)
    camera_brand.save()
    return redirect(url_for("administration.camera_settings.brands_index"))


@module.route("/brands/<brand_id>/delete", methods=["GET", "POST"])
@acl.admin_permission.require(http_exception=403)
def delete_brand(brand_id):
    camera_brand = models.CameraBrand.objects(id=brand_id).delete()
    return redirect(url_for("administration.camera_settings.brands_index"))


@module.route("/brands/<brand_id>/models")
@acl.admin_permission.require(http_exception=403)
def models_index(brand_id):
    brand = models.CameraBrand.objects.get(id=brand_id)
    camera_models = models.CameraModel.objects(brand=brand)
    return render_template(
        "/cameras/models_list.html", camera_models=camera_models, brand=brand
    )


@module.route("/brands/<brand_id>/models/create", methods=["GET", "POST"])
@acl.admin_permission.require(http_exception=403)
def create_models(brand_id):
    brand = models.CameraBrand.objects.get(id=brand_id)
    # camera_models = models.CameraModel.objects(brand=brand)
    form = forms.cameras.CameraModelForm()
    if not form.validate_on_submit():
        return render_template(
            "/cameras/create-edit_models.html",
            form=form,
            brand=brand,
        )
    camera_model = models.CameraModel(brand=brand)

    form.populate_obj(camera_model)
    camera_model.save()
    return redirect(
        url_for(
            "administration.camera_settings.models_index",
            brand_id=brand_id,
        )
    )


@module.route(
    "/brands/<brand_id>/models/<camera_model_id>/update", methods=["GET", "POST"]
)
@acl.admin_permission.require(http_exception=403)
def edit_model(brand_id, camera_model_id):
    brand = models.CameraBrand.objects.get(id=brand_id)
    camera_model = models.CameraModel.objects.get(id=camera_model_id)
    form = forms.cameras.CameraModelForm(obj=camera_model)
    if not form.validate_on_submit():
        return render_template(
            "/cameras/create-edit_models.html",
            form=form,
            brand=brand,
            camera_model=camera_model,
        )
    # camera_model = models.CameraModel(brand=brand)
    form.populate_obj(camera_model)
    camera_model.save()
    return redirect(
        url_for(
            "administration.camera_settings.models_index",
            brand_id=brand_id,
        )
    )


@module.route(
    "/brands/<brand_id>/models/<camera_model_id>/delete", methods=["GET", "POST"]
)
@acl.admin_permission.require(http_exception=403)
def delete_model(brand_id, camera_model_id):
    # brand = models.CameraBrand.objects.get(id=brand_id)
    camera_model = models.CameraModel.objects(id=camera_model_id)
    camera_model.delete()
    return redirect(
        url_for(
            "administration.camera_settings.models_index",
            brand_id=brand_id,
        )
    )
