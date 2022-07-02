from .server import ComputeNodeServer


def create_server():
    from nokkhum.utils import config

    settings = config.get_settings()
    server = ComputeNodeServer(settings)

    return server
