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
)

from flask_login import login_required, current_user
import pathlib

from nokkhum import models

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
    date_dirs = [p for p in processor_path.iterdir() if p.is_dir()]
    return date_dirs


def get_file_by_dir_date(processor_id, date_dir):
    root = get_storage_path()
    processor_path = root / processor_id / date_dir
    file_list = [p for p in processor_path.iterdir() if p.suffix != ".png"]
    return file_list


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
    return render_template(
        "/storages/list_storage_by_processor.html",
        date_dirs=date_dirs,
        processor=processor,
        camera=processor.camera,
    )


@module.route("/processors/<processor_id>/<date_dir>")
@login_required
def list_records_by_date(processor_id, date_dir):
    file_list = get_file_by_dir_date(processor_id, date_dir)
    file_list.sort(reverse=True)
    processor = models.Processor.objects.get(id=processor_id)
    return render_template(
        "/storages/list_records_by_date.html",
        file_list=file_list,
        date_dir=date_dir,
        processor=processor,
        camera=processor.camera,
    )


@module.route("/processors/<processor_id>/<date_dir>/view/<filename>")
@login_required
def view_video(processor_id, date_dir, filename):
    video_path = get_video_path(processor_id, date_dir, filename)

    processor = models.Processor.objects.get(id=processor_id)
    return render_template(
        "/storages/view_video.html",
        video_path=video_path,
        processor=processor,
        camera=processor.camera,
    )


@module.route("/processors/<processor_id>/<date_dir>/<filename>")
@login_required
def download(processor_id, date_dir, filename):

    if filename.startswith("_"):
        abort(404)
    media_path = get_video_path(processor_id, date_dir, filename)
    suffix = media_path.suffix[1:]
    if suffix in ["png"]:
        return send_file(str(media_path), mimetype=f"image/{suffix}")
    elif suffix in ["mp4"]:
        return send_file(str(media_path), mimetype=f"video/{suffix}")
