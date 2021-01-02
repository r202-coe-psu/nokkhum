__version__ = "0.0.1"

import optparse

from quart import Quart, g
import asyncio

from nokkhum import models, default_settings
from nokkhum.utils import config

from . import live_streaming
from .subscribers import StreamingSubscriber


def create_app():
    app = Quart(__name__)
    app.config.from_object(default_settings)
    app.config.from_envvar("NOKKHUM_SETTINGS", silent=True)

    # models.init_db(app)
    app.register_blueprint(live_streaming.module)
    app.queues = {}
 
    @app.before_serving
    async def before():
        settings = config.get_settings()
        streaming_sub = StreamingSubscriber(app.queues, settings)
        await streaming_sub.set_up()
        app.streaming_sub = streaming_sub

    return app


def get_program_options(default_host="127.0.0.1", default_port="8081"):

    """
    Takes a quart.Quart instance and runs it. Parses
    command-line flags to configure the app.
    """

    # Set up the command-line options
    parser = optparse.OptionParser()
    parser.add_option(
        "-H",
        "--host",
        help="Hostname of the Quart app " + "[default %s]" % default_host,
        default=default_host,
    )
    parser.add_option(
        "-P",
        "--port",
        help="Port for the Quart app " + "[default %s]" % default_port,
        default=default_port,
    )

    # Two options useful for debugging purposes, but
    # a bit dangerous so not exposed in the help message.
    parser.add_option(
        "-c", "--config", dest="config", help=optparse.SUPPRESS_HELP, default=None
    )
    parser.add_option(
        "-d", "--debug", action="store_true", dest="debug", help=optparse.SUPPRESS_HELP
    )
    parser.add_option(
        "-p",
        "--profile",
        action="store_true",
        dest="profile",
        help=optparse.SUPPRESS_HELP,
    )

    options, _ = parser.parse_args()

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if options.profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware

        app.config["PROFILE"] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[30])
        options.debug = True

    return options
