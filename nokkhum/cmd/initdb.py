import os

import flask
from yana import models


def init_admin():
    user_count = models.User.objects().count()
    if user_count > 0:
        print('System already has user.')
        return

    admin = models.User(email='admin@system.local',
                        first_name='Admin',
                        last_name='ADMIN',
                        organization='SYSTEM ADMIN')
    admin.set_password('p@ssw0rd')
    admin.roles.append('admin')
    admin.status = 'active'
    admin.save()
    print('Default email is', admin.email, ', password is p@ssw0rd')


def main():
    filename = os.environ.get('YANA_SETTINGS', None)

    if filename is None:
        print('This program require YANA_SETTINGS environment')
        return
    print(filename)

    file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), '../../')

    settings = flask.config.Config(file_path)
    settings.from_object('yana.default_settings')
    settings.from_envvar('YANA_SETTINGS', silent=True)

    models.init_mongoengine(settings)
    init_admin()
