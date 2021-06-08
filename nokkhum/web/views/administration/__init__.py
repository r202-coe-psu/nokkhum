from flask import Blueprint

from nokkhum.web import acl
from . import projects

module = Blueprint("administration", __name__, url_prefix="/administration")
views = [projects]


@module.route("/")
@acl.officer_permission.require(http_exception=403)
def index():
    return "administration"
