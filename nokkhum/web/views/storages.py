from nokkhum.models import storages
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    send_file,
    make_response,
    current_app,
    abort,
    Response,
)

from flask_login import login_required, current_user
import pathlib

from nokkhum import models
from nokkhum.web import nats
from .. import forms

# import asyncio
import datetime


module = Blueprint("storages", __name__, url_prefix="/storages")


def get_storage_path():
    root_name = current_app.config.get("NOKKHUM_PROCESSOR_RECORDER_PATH")
    return pathlib.Path(root_name)


def get_dir_by_processor(processor_id):
    root = get_storage_path()
    processor_path = root / processor_id
    if not processor_path.is_dir():
        processor_path.mkdir(parents=True)
    date_dirs = [p for p in processor_path.iterdir() if p.is_dir() and p.name.isdigit()]
    return date_dirs


def get_file_by_dir_date(processor_id, date_dir):
    root = get_storage_path()
    video_path = root / processor_id / date_dir
    if not video_path.exists():
        return {}
    file_dict = {}
    for p in video_path.iterdir():
        if p.suffix == ".png":
            video_zip = f"{p.stem.replace('-thumbnail','')}.tar.{current_app.config.get('TAR_TYPE')}"
            if not (video_path / video_zip).exists():
                file_dict[p.name] = "Recording"
            else:
                file_dict[p.name] = video_zip
    # print(file_dict)
    return file_dict


def get_video_path(processor_id, date_dir, filename):
    root = get_storage_path()
    video_path = root / processor_id / date_dir / filename
    return video_path


@module.route("/")
@login_required
def index():
    return render_template("/storages/index.html")


@module.route("/processors/<processor_id>")
@login_required
def list_storage_by_processor(processor_id):
    date_dirs = get_dir_by_processor(processor_id)
    date_dirs.sort(reverse=True)
    processor = models.Processor.objects.get(id=processor_id)
    if not processor.camera.project.is_member(current_user._get_current_object()):
        return redirect(url_for("dashboard.index"))
    return render_template(
        "/storages/list_storage_by_processor.html",
        date_dirs=date_dirs,
        processor=processor,
        camera=processor.camera,
    )


@module.route("/processors/<processor_id>/<date_dir>")
@login_required
def list_records_by_date(processor_id, date_dir):
    file_dict = get_file_by_dir_date(processor_id, date_dir)
    # file_list.sort(reverse=True)
    processor = models.Processor.objects.get(id=processor_id)
    if not processor.camera.project.is_member(current_user._get_current_object()):
        storage_share_list = models.StorageShare.objects(
            psu_passport_username=current_user._get_current_object().username,
            start_date__lte=datetime.date.today(),
            expire_date__gte=datetime.date.today(),
        ).first()
        if storage_share_list:
            pass
        else:
            return redirect(url_for("dashboard.index"))
    return render_template(
        "/storages/list_records_by_date.html",
        file_dict=file_dict,
        date_dir=date_dir,
        processor=processor,
        camera=processor.camera,
    )


@module.route("share/processors/<processor_id>/<date_dir>", methods=["GET", "POST"])
@login_required
def share_storage(processor_id, date_dir):
    processor = models.Processor.objects.get(id=processor_id)
    if not processor.camera.project.is_assistant_or_owner_or_security_guard(
        current_user._get_current_object()
    ):
        return redirect(url_for("dashboard.index"))

    form = forms.storages.ShareStorageForm()
    users = models.User.objects(status="active")
    storage_share_list = models.StorageShare.objects(
        processor=processor, date_dir=date_dir, expire_date__gte=datetime.date.today()
    )
    if not form.validate_on_submit():
        return render_template(
            "/storages/share_storage.html",
            date_dir=date_dir,
            processor=processor,
            camera=processor.camera,
            users=users,
            form=form,
            storage_share=storage_share_list,
        )

    storage_share = models.StorageShare.objects(
        processor=processor,
        date_dir=date_dir,
        psu_passport_username=form.psu_passport_username.data,
    ).first()
    if not storage_share:
        storage_share = models.StorageShare(
            processor=processor,
            date_dir=date_dir,
            psu_passport_username=form.psu_passport_username.data,
        )

    storage_share.start_date = datetime.datetime.strptime(
        form.start_date.data, "%d/%m/%Y"
    ).date()
    storage_share.expire_date = datetime.datetime.strptime(
        form.expire_date.data, "%d/%m/%Y"
    ).date()
    storage_share.save()
    return redirect(
        url_for("storages.share_storage", processor_id=processor_id, date_dir=date_dir)
    )


@module.route(
    "share/processors/<processor_id>/<date_dir>/<username>/remove",
    methods=["GET"],
)
@login_required
def remove_share_storage(processor_id, date_dir, username):
    processor = models.Processor.objects.get(id=processor_id)
    # print(file_list)
    if not processor.camera.project.is_assistant_or_owner_or_security_guard(
        current_user._get_current_object()
    ):
        return redirect(url_for("dashboard.index"))

    storage_share = models.StorageShare.objects(
        processor=processor,
        date_dir=date_dir,
        psu_passport_username=username,
    ).first()
    if not storage_share:
        return redirect(url_for("dashboard.index"))

    storage_share.delete()
    return redirect(
        url_for("storages.share_storage", processor_id=processor_id, date_dir=date_dir)
    )


@module.route("/processors/<processor_id>/<date_dir>/view/<filename>")
@login_required
def view_video(processor_id, date_dir, filename):
    video_path = get_video_path(processor_id, date_dir, filename)
    processor = models.Processor.objects.get(id=processor_id)
    if not processor.camera.project.is_member(current_user._get_current_object()):
        storage_share_list = models.StorageShare.objects(
            psu_passport_username=current_user._get_current_object().username,
            start_date__lte=datetime.date.today(),
            expire_date__gte=datetime.date.today(),
        ).first()
        if storage_share_list:
            pass
        else:
            return redirect(url_for("dashboard.index"))
    return render_template(
        "/storages/view_video.html",
        video_path=video_path,
        processor=processor,
        camera=processor.camera,
    )


@module.route("/processors/<processor_id>/<date_dir>/<filename>")
@login_required
def download_tar(processor_id, date_dir, filename):
    processor = models.Processor.objects.get(id=processor_id)
    if not processor.camera.project.is_member(current_user._get_current_object()):
        storage_share_list = models.StorageShare.objects(
            psu_passport_username=current_user._get_current_object().username,
            start_date__lte=datetime.date.today(),
            expire_date__gte=datetime.date.today(),
        ).first()
        if storage_share_list:
            pass
        else:
            # return redirect(url_for("dashboard.index"))
            return Response(403)
    if filename.startswith("_"):
        abort(404)
    media_path = get_video_path(processor_id, date_dir, filename)
    return send_file(str(media_path), mimetype="application/x-xz")


@module.route("/processors/<processor_id>/<date_dir>/thumbnails/<filename>")
@login_required
def get_thumbnail(processor_id, date_dir, filename):
    processor = models.Processor.objects.get(id=processor_id)
    if not processor.camera.project.is_member(current_user._get_current_object()):
        storage_share_list = models.StorageShare.objects(
            psu_passport_username=current_user._get_current_object().username,
            start_date__lte=datetime.date.today(),
            expire_date__gte=datetime.date.today(),
        ).first()
        if storage_share_list:
            pass
        else:
            # return redirect(url_for("dashboard.index"))
            return Response(403)
    if filename.startswith("_"):
        abort(404)
    media_path = get_video_path(processor_id, date_dir, filename)
    suffix = media_path.suffix[1:]
    return send_file(str(media_path), mimetype=f"image/{suffix}")
