from .server import ProcessorServer


def create_server():
    from nokkhum.utils import config

    settings = config.get_settings()
    server = ProcessorServer(settings)

    return server
