from flask import Blueprint

from nokkhum.web import acl
from . import projects
from . import camera_settings

module = Blueprint("administration", __name__, url_prefix="/administration")
views = [projects, camera_settings]


@module.route("/")
@acl.officer_permission.require(http_exception=403)
def index():
    return "administration"
