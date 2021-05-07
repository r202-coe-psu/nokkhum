__version__ = '0.0.1'

import asyncio
from nats.aio.client import Client as NATS
import optparse

from flask import Flask, Blueprint

from .. import models
from . import views
from . import acl
from . import nats
from . import oauth2


# async def setup_nats(app):
#     nc = NATS()
#     await nc.connect(app.config.get('YANA_MESSAGE_NATS_HOST'), app.loop)
#     app.nc = nc


def create_app():
    app = Flask(__name__)
    app.config.from_object('nokkhum.default_settings')
    app.config.from_envvar('NOKKHUM_SETTINGS', silent=True)

    models.init_db(app)
    acl.init_acl(app)
    oauth2.init_oauth(app)
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)

    # app.loop = loop
    # loop.run_until_complete(setup_nats(app))

    views.register_blueprint(app)

    static_bp = Blueprint(
            'static.data',
            __name__,
            static_folder=app.config.get('NOKKHUM_PROCESSOR_RECORDER_PATH'),
            static_url_path='/static/data')
    app.register_blueprint(static_bp)

    nats.init_nats(app)

    return app


def get_program_options(default_host='127.0.0.1',
                        default_port='8080'):

    """
    Takes a flask.Flask instance and runs it. Parses 
    command-line flags to configure the app.
    """

    # Set up the command-line options
    parser = optparse.OptionParser()
    parser.add_option("-H", "--host",
                      help="Hostname of the Flask app " + \
                           "[default %s]" % default_host,
                      default=default_host)
    parser.add_option("-P", "--port",
                      help="Port for the Flask app " + \
                           "[default %s]" % default_port,
                      default=default_port)

    # Two options useful for debugging purposes, but 
    # a bit dangerous so not exposed in the help message.
    parser.add_option("-c", "--config",
                      dest="config",
                      help=optparse.SUPPRESS_HELP, default=None)
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug",
                      help=optparse.SUPPRESS_HELP)
    parser.add_option("-p", "--profile",
                      action="store_true", dest="profile",
                      help=optparse.SUPPRESS_HELP)

    options, _ = parser.parse_args()

    # If the user selects the profiling option, then we need
    # to do a little extra setup
    if options.profile:
        from werkzeug.contrib.profiler import ProfilerMiddleware

        app.config['PROFILE'] = True
        app.wsgi_app = ProfilerMiddleware(app.wsgi_app,
                                          restrictions=[30])
        options.debug = True

    return options

