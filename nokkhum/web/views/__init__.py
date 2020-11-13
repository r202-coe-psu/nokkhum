from . import site
from . import accounts
from . import dashboard
from . import projects
from . import cameras
from . import processors
from . import maps
from . import storages
from . import gridviews


def get_subblueprints(views=[]):
    blueprints = []
    for view in views:
        blueprints.append(view.module)
        if "subviews" in dir(view):
            for module in get_subblueprints(view.subviews):
                if view.module.url_prefix and module.url_prefix:
                    module.url_prefix = view.module.url_prefix + module.url_prefix
                blueprints.append(module)
    return blueprints


def register_blueprint(app):
    blueprints = get_subblueprints(
        [
            site,
            accounts,
            dashboard,
            projects,
            cameras,
            processors,
            maps,
            storages,
            gridviews,
        ]
    )

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
