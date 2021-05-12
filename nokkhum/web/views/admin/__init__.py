from flask import Blueprint

from yana.web import acl

module = Blueprint('admin', __name__, url_prefix='/admin')



@module.route('/')
def index():
    return 'admin'
